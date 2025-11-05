import requests
from urllib.parse import urlparse, parse_qs
import re
from bs4 import BeautifulSoup

class BibliotekDK:
    def __init__(self, agency: str):
        self.agency = agency
        if not agency:
            raise ValueError("agency must be provided")
        if not int(agency.isdigit()):
            raise ValueError("agency must be a numeric string representing the agency ID")
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)",
            "Accept": "*/*",
            "DNT": "1",
            "Sec-GPC": "1",
        })
        self.graphql_url = "https://bibliotek.dk/api/bibdk21/graphql"

    def login(self, user_id: str, pincode: str):
        if user_id is None or pincode is None:
            raise ValueError("user id and pincode must be provided")
        if not user_id.strip() or not pincode.strip():
            raise ValueError("user id and pincode cannot be empty")
        
        # csrf token: available via GET 🤡
        # devs really said "security theater, but make it RESTful"
        csrf = self.session.get("https://bibliotek.dk/api/auth/csrf").json()["csrfToken"]

        signin = self.session.post(
            f"https://bibliotek.dk/api/auth/signin/adgangsplatformen?agency={self.agency}&force_login=1",
            data={
                "callbackUrl": f"https://bibliotek.dk/?setPickupAgency={self.agency}",
                "csrfToken": csrf,
                "json": "true",
            },
        ).json()
        redirect_url = signin["url"]

        r1 = self.session.get(redirect_url, allow_redirects=True)
        html = r1.text

        match = re.search(r'action="(/login/identityProviderCallback/[^"]+)"', html)
        if not match: # fallback
            soup = BeautifulSoup(html, "html.parser")
            form = soup.find("form", action=re.compile("identityProviderCallback"))
            if form:
                match = re.match(r"(/login/identityProviderCallback/[^?]+)", form["action"])
        if not match:
            raise Exception("couldn't locate identityProviderCallback form on login page")

        callback_path = "https://login.bib.dk" + match.group(1)

        data = {
            "agency": self.agency,
            #"libraryName": "Odense",
            "loginBibDkUserId": user_id,
            "pincode": pincode,
        }
        login_res = self.session.post(callback_path, data=data, allow_redirects=False)
        if "location" not in login_res.headers:
            raise Exception("problem logging in. wrong creds or unexpected response.")

        next1 = "https://login.bib.dk" + login_res.headers["location"]
        r2 = self.session.get(next1, allow_redirects=False)
        final = r2.headers.get("location")
        if final:
            self.session.get(final, allow_redirects=False)

        token = self.session.cookies.get("next-auth.session-token")
        if not token:
            raise Exception("no session token after login!")
        return token
    
    def _graphql(self, query: str, variables: dict = None):
        headers = {
            "Content-Type": "application/json",
            "Origin": "https://bibliotek.dk",
            "Referer": "https://bibliotek.dk/profil/laan-og-reserveringer",
        }
        r = self.session.post(self.graphql_url, json={"query": query, "variables": variables or {}}, headers=headers)
        r.raise_for_status()
        return r.json().get("data")

    def get_loans(self):
        q = """
        query UserLoans {
          user {
            loans {
              result {
                agencyId
                loanId
                title
                creator
                dueDate
              }
            }
          }
        }
        """
        data = self._graphql(q)
        return data["user"]["loans"]["result"]

    def get_reservations(self):
        q = """
        query UserOrders {
        user {
            orders {
            result {
                agencyId
                orderId
                title
                creator
                orderDate
                pickUpBranch { agencyName }
            }
            }
        }
        }
        """
        data = self._graphql(q)
        return data["user"]["orders"]["result"]
    
    def get_user_info(self):
        query = """
        query BasicUser {
        user {
            name
            mail
            address
            postalCode
            isCPRValidated
            loggedInAgencyId
            loggedInBranchId
            municipalityAgencyId
            omittedCulrData {
            hasOmittedCulrUniqueId
            hasOmittedCulrMunicipality
            hasOmittedCulrMunicipalityAgencyId
            hasOmittedCulrAccounts
            }
            rights {
            infomedia
            digitalArticleService
            demandDrivenAcquisition
            }
            agencies {
            id
            name
            type
            hitcount
            user { mail }
            result {
                branchId
                agencyId
                agencyName
                agencyType
                name
                branchWebsiteUrl
                pickupAllowed
                borrowerCheck
                culrDataSync
            }
            }
        }
        }
        """

        r = self.session.post(
            "https://bibliotek.dk/api/bibdk21/graphql",
            json={"query": query, "variables": {}},
            headers={
                "Content-Type": "application/json",
                "Origin": "https://bibliotek.dk",
                "X-Tracking-Consent": "false",
                "DNT": "1",
                "Sec-GPC": "1"
            }
        )
        r.raise_for_status()
        data = r.json().get("data", {}).get("user")
        return data
    
    def renew_loan(self, loan_id: str, agency_id: str):
        query = """
        mutation renewLoan($loanId: String!, $agencyId: String!) {
        renewLoan(loanId: $loanId, agencyId: $agencyId, dryRun: false) {
            renewed
            error
            dueDate
        }
        }
        """
        vars = {"loanId": loan_id, "agencyId": agency_id}
        url = "https://bibliotek.dk/api/SimpleSearch/graphql"
        headers = {
            "Content-Type": "application/json",
            "Origin": "https://bibliotek.dk",
            "Referer": "https://bibliotek.dk/profil/laan-og-reserveringer",
            "X-Tracking-Consent": "false",
            "DNT": "1",
            "Sec-GPC": "1"
        }
        r = self.session.post(url, json={"query": query, "variables": vars}, headers=headers)
        r.raise_for_status()
        data = r.json().get("data", {}).get("renewLoan")
        return data
    
    def renew_all(self):
        loans = self.get_loans()
        results = []
        for l in loans:
            loan_id = l["loanId"]
            agency_id = l["agencyId"]
            res = self.renew_loan(loan_id, agency_id)
            results.append({"loanId": loan_id, **res})
        return results

class AgencyHelper:
    @staticmethod
    def search(query: str, limit: int = 50):
        q = """
        query LibraryFragmentsSearch($q: String, $limit: PaginationLimitScalar, $language: LanguageCodeEnum) {
        branches(q: $q, language: $language, limit: $limit, bibdkExcludeBranches:true, statuses:AKTIVE, sortPickupAllowed: true) {
            hitcount
            result {
            agencyName
            name
            agencyType
            branchId
            agencyId
            city
            postalAddress
            postalCode
            pickupAllowed
            branchWebsiteUrl
            }
        }
        }
        """
        variables = {"q": query, "language": "DA", "limit": limit}
        res = requests.post(
            "https://bibliotek.dk/api/bibdk21/graphql",
            json={"query": q, "variables": variables},
            headers={
                "Content-Type": "application/json",
                "Origin": "https://bibliotek.dk",
                "Referer": "https://bibliotek.dk",
            },
        )
        res.raise_for_status()
        data = res.json().get("data", {}).get("branches", {})
        return data.get("result", [])