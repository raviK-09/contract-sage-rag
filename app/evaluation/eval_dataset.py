"""
Curated ground-truth Q&A pairs for evaluating the RAG pipeline.

Each item has: question, ground_truth, expected_doc, expected_keywords,
category, and should_decline flag.
"""

EVAL_DATASET = [
    # ── Residential Rental Agreement ─────────────────────────────────────────
    {
        "question": "What is the monthly rent amount and when is it due each month?",
        "ground_truth": "The monthly rent is Rs. 28,000 and it is due on the 5th of each month via electronic bank transfer.",
        "expected_doc": "residential_rental_agreement.pdf",
        "expected_keywords": ["28,000", "5th", "bank transfer"],
        "category": "Rent & Payment",
        "should_decline": False,
    },
    {
        "question": "What is the security deposit amount and when is it refunded?",
        "ground_truth": "The security deposit is Rs. 56,000 (two months rent) and must be refunded within 60 days of vacating after deducting any dues.",
        "expected_doc": "residential_rental_agreement.pdf",
        "expected_keywords": ["56,000", "60 days"],
        "category": "Security Deposit",
        "should_decline": False,
    },
    {
        "question": "How much notice must either party give to terminate the rental agreement?",
        "ground_truth": "Either party must give 2 months prior written notice to terminate the agreement.",
        "expected_doc": "residential_rental_agreement.pdf",
        "expected_keywords": ["2 months", "notice", "written"],
        "category": "Termination",
        "should_decline": False,
    },
    {
        "question": "What happens to the security deposit if the tenant breaks the lock-in period?",
        "ground_truth": "If the tenant vacates during the lock-in period, the security deposit is forfeited entirely.",
        "expected_doc": "residential_rental_agreement.pdf",
        "expected_keywords": ["forfeited", "lock-in"],
        "category": "Termination",
        "should_decline": False,
    },

    # ── Employment Agreement ──────────────────────────────────────────────────
    {
        "question": "What is the employee's total annual CTC in the employment agreement?",
        "ground_truth": "The employee's total annual CTC (Cost to Company) is Rs. 24,00,000.",
        "expected_doc": "employment_agreement.pdf",
        "expected_keywords": ["24,00,000", "CTC"],
        "category": "Compensation",
        "should_decline": False,
    },
    {
        "question": "What is the non-compete restriction period after leaving the company?",
        "ground_truth": "The non-compete restriction is 12 months after the termination of employment.",
        "expected_doc": "employment_agreement.pdf",
        "expected_keywords": ["12 months", "non-compete"],
        "category": "Restrictions",
        "should_decline": False,
    },
    {
        "question": "Does the IP assignment clause cover work done outside office hours?",
        "ground_truth": "Yes, the IP assignment clause is broad and covers intellectual property created using company resources or related to company business, which may include personal projects.",
        "expected_doc": "employment_agreement.pdf",
        "expected_keywords": ["intellectual property", "resources"],
        "category": "IP Rights",
        "should_decline": False,
    },

    # ── Mutual NDA ────────────────────────────────────────────────────────────
    {
        "question": "How long does the confidentiality obligation survive after the NDA ends?",
        "ground_truth": "The confidentiality obligations survive for 5 years after the termination of the agreement.",
        "expected_doc": "mutual_nda_agreement.pdf",
        "expected_keywords": ["5 years", "survive", "confidentiality"],
        "category": "Confidentiality",
        "should_decline": False,
    },

    # ── Commercial Lease ──────────────────────────────────────────────────────
    {
        "question": "What is the annual rent escalation percentage in the commercial lease?",
        "ground_truth": "The annual rent escalation is 8% per year.",
        "expected_doc": "commercial_lease_agreement.pdf",
        "expected_keywords": ["8%", "escalation"],
        "category": "Rent & Payment",
        "should_decline": False,
    },

    # ── Freelance Agreement ───────────────────────────────────────────────────
    {
        "question": "When does IP ownership transfer from the freelancer to the client?",
        "ground_truth": "IP ownership transfers to the client only upon full and final payment of all invoices.",
        "expected_doc": "freelance_service_agreement.pdf",
        "expected_keywords": ["payment", "IP", "transfer"],
        "category": "IP Rights",
        "should_decline": False,
    },

    # ── Out-of-scope (must decline) ───────────────────────────────────────────
    {
        "question": "What is the current stock price of NovaTech Solutions?",
        "ground_truth": "DECLINE — this information is not in the uploaded contracts.",
        "expected_doc": None,
        "expected_keywords": [],
        "category": "Out-of-scope",
        "should_decline": True,
    },
    {
        "question": "What is the weather forecast for Bangalore this weekend?",
        "ground_truth": "DECLINE — this information is not in the uploaded contracts.",
        "expected_doc": None,
        "expected_keywords": [],
        "category": "Out-of-scope",
        "should_decline": True,
    },
]
