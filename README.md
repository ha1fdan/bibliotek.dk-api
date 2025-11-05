# bibliotek.dk-api
Unofficial Python API for Denmark’s library system (bibliotek.dk).

> ⚠️ Not affiliated with DBC.dk, bibliotek.dk, or any library. For prototyping/edu only.

## Example Usage
For a quickstart, see [example.py](/example.py), remember to set up your `.env` file based on [.env.example](/.env.example).

```bash
python3 example.py
Name: [beskyttet]
Email: someone@example.com
Rights: {'infomedia': True, 'digitalArticleService': True, 'demandDrivenAcquisition': True}
Branches: ['Bolbro Bibliotek', 'Dalum Bibliotek', 'Holluf Pile Bibliotek', 'Højby Bibliotek', 'Korup Bibliotek', 'Lokalhistorisk Bibliotek', 'Odense Bibliotekerne', 'Tarup Bibliotek', 'Vollsmose Bibliotek']


Loans:
Borat : cultural learnings of America for make benefit glorious nation of Kazakhstan - due 2025-11-12T23:00:00.000Z
Hacker - due 2025-11-11T23:00:00.000Z
No reservations


Renewal results:
Loan 4277409793 renewal failed: Item not renewable
Loan 5221812702 renewal failed: Item not renewable
```

## Features
- [x] User authentication with CPR number or library user ID and pincode.
- [x] Fetch user information including name, email, rights, and associated library branches.
- [x] List current loans with details such as title and due date.
- [x] List current reservations with details such as title and pickup location.
- [x] Renew loans with feedback on success or failure.
- [x] Search for libraries by name to retrieve agency IDs.

## Installation
```bash
git clone https://github.com/ha1fdan/bibliotek.dk-api
cd bibliotek.dk-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Contribution
Contributions are welcome! Please open issues or pull requests!

## License
This project is licensed under the [MIT License](./LICENSE).
