"""Words and pictures of the 2026-11 portal guide, shared by the deck and the Word builders.

Plain English only: short sentences and everyday words. Rules come from docs/PORTAL_RULES.md.
Each page has: part, title, role ("partner", "dbgi", or None), and optionally intro, steps, tip, warn,
pics [(crop name, caption)], table (rows, first row is the header), widths (shares of the table width), flow.
"""

TITLE = "Using the DBGI Portal"
SUBTITLE = "A step-by-step guide for partners and DBGI staff"
SAMPLE_NOTE = (
    "All companies, people, and prices in this guide are examples. "
    "The sample end-user is the City of Lucena Mayor's Office."
)

PARTS = {
    0: "Start here",
    1: "Getting started",
    2: "Register a deal",
    3: "Follow your deal",
    4: "Review a deal",
    5: "Fix a returned deal",
    6: "Confirm the deal",
    7: "Approve the price",
    8: "See the result",
    9: "Change a deal",
    10: "Withdraw a deal",
    11: "Report the result",
    12: "Time limits",
    13: "Other DBGI tasks",
    14: "Repeat orders",
    15: "Quick help",
}

PAGES = [
    {
        "part": 0,
        "title": "What is this portal for?",
        "role": None,
        "intro": "Use it to tell DBGI about a government project before the bid.",
        "table": [
            ["Who", "What they do in the portal"],
            [
                "Partner",
                "Registers deals, follows them, asks for price renewals, reports the result",
            ],
            ["DBGI", "Checks deals, confirms the project, decides prices, keeps the rankings"],
        ],
        "widths": [1, 4],
        "tip": "Each company sees only its own deals, ranks, and prices. No company can see another company's.",
    },
    {
        "part": 0,
        "title": "The journey of a deal",
        "role": None,
        "intro": "Every deal follows the same path. The parts of this guide follow it too.",
        "flow": [
            ("Partner registers the deal", "partner"),
            ("DBGI reviews it", "dbgi"),
            ("DBGI confirms the project. The deal is Registered and gets a rank.", "dbgi"),
            ("DBGI decides the price", "dbgi"),
            ("Partner sees the price and can ask to renew it", "partner"),
            ("Partner reports if the project was won or lost", "partner"),
        ],
    },
    {
        "part": 0,
        "title": "Our example deal",
        "role": None,
        "intro": "We follow one deal from start to finish.",
        "table": [
            ["Detail", "Example"],
            ["End-user (the government buyer)", "City of Lucena Mayor's Office"],
            ["Project", "20 laser printers for the Mayor's Office"],
            ["Product", "M1820W, 20 ppm monochrome laser printer"],
            ["List price", "10,000.00 each"],
            ["Price the partner asks for", "9,000.00 each"],
            ["Competitor", "Canon imageCLASS LBP246dw at 9,300.00"],
        ],
        "widths": [2, 3],
        "tip": "All prices in the portal include VAT.",
    },
    # Part 1
    {
        "part": 1,
        "title": "Sign in",
        "role": "both",
        "steps": [
            "Open the portal link.",
            "Type the username and password DBGI gave you.",
            "Click **Sign in**.",
        ],
        "pics": [("login", "The sign-in page")],
        "tip": "Forgot your password? Ask your DBGI administrator. Do not share your account.",
    },
    {
        "part": 1,
        "title": "Your list of deals",
        "role": "partner",
        "intro": "After you sign in, you see all your company's deals.",
        "steps": [
            "Each row is one deal.",
            "Click the blue reference number to open a deal.",
            "Use the search box and filters to find a deal.",
            "Click **New registration** to add a deal.",
        ],
        "pics": [("list", "The deal list")],
    },
    {
        "part": 1,
        "title": "Find help and messages",
        "role": "both",
        "steps": [
            "Click **Help** in the top menu for short steps inside the portal.",
            "Click **Notifications** to read your messages.",
            "Click **Rankings** to see your place on a project.",
        ],
        "pics": [("help", "The Help page")],
    },
    # Part 2
    {
        "part": 2,
        "title": "Step 1: Who is the buyer?",
        "role": "partner",
        "steps": [
            "Click **New registration**.",
            "In **End-user**, type the buyer's name and choose it.",
            "Not in the list? Click **Add missing end-user**. DBGI will check it.",
            "Type the project title, bid date, and delivery date.",
            "Check your contact details. They are filled in for you.",
        ],
        "pics": [("form-top", "End-user, project, and contact details")],
    },
    {
        "part": 2,
        "title": "Step 2: Who are you up against?",
        "role": "partner",
        "steps": [
            "Click **Add competitor**.",
            "Type the brand and the model.",
            "Type the price they offered in **Bid price**.",
            "Click **Save item**.",
        ],
        "pics": [("competitor", "Adding a competitor")],
        "tip": "More than one competitor? Click **Add competitor** again.",
    },
    {
        "part": 2,
        "title": "Step 3: What do you want to sell?",
        "role": "partner",
        "steps": [
            "Click **Add product**.",
            "Choose the product. If it is not listed, choose **Not in catalog** and describe it.",
            "Type the quantity and the price you are asking for.",
            "Say why you need this price in **Justification**.",
            "Click **Save item**.",
        ],
        "pics": [("product", "Adding a product")],
        "warn": "The price you type is only a request. It is not approved until DBGI says so.",
    },
    {
        "part": 2,
        "title": "Step 4: Add your proof and send",
        "role": "partner",
        "steps": [
            "Describe your proof, like a request for quotation.",
            "Add a link or click **Add files**.",
            "Tick the box to confirm you may share it.",
            "Click **Create registration**.",
        ],
        "pics": [("form-attachment", "The attachment section and the Create registration button")],
        "warn": "Do not upload other companies' prices or bids, IDs, signatures, or private personal details.",
    },
    {
        "part": 2,
        "title": "Why you should register early",
        "role": "partner",
        "intro": (
            "The portal records the exact time you send your deal. This time decides your place in line "
            "for the project. Nobody can change it, and later edits do not change it."
        ),
        "pics": [("submitted-top", "Your new deal, with the status Submitted")],
        "tip": "A partner that registers first gets rank 1 once DBGI confirms the deal. Rank 1 gets the best price.",
    },
    # Part 3
    {
        "part": 3,
        "title": "Read your deal page",
        "role": "partner",
        "steps": [
            "The labels at the top show the deal, the project, and the price status.",
            "**What happens next?** tells you the next step.",
            "**Commercial approvals** shows DBGI's price decision.",
            "**Activity** shows everything that happened, who did it, and when.",
        ],
        "pics": [
            ("sub-next", "What happens next"),
            ("sub-approvals", "Commercial approvals: DBGI has not decided yet"),
            ("sub-activity", "Activity"),
        ],
    },
    {
        "part": 3,
        "title": "What each status means",
        "role": "partner",
        "table": [
            ["Status", "What it means", "What happens next"],
            ["Submitted", "DBGI received your deal", "DBGI starts the review"],
            ["Under review", "DBGI is checking it", "DBGI decides"],
            ["Returned for changes", "DBGI needs you to fix something", "You edit and save"],
            ["Resubmitted", "You sent your fixes", "DBGI checks again"],
            ["Registered", "DBGI confirmed the project. You have a rank.", "Price decision"],
            [
                "Review required after edit",
                "You changed a Registered deal",
                "DBGI checks again. Your rank stays.",
            ],
            ["Rejected", "DBGI said no. The reason is in Activity.", "This is final"],
            ["Withdrawn", "You took the deal back", "This is final"],
        ],
        "widths": [3, 5, 4],
    },
    {
        "part": 3,
        "title": "Your messages",
        "role": "partner",
        "steps": [
            "Everyone in your company sees portal messages about your deals.",
            "The person who registered the deal also gets an email.",
            "Click **View registration** to open the deal.",
        ],
        "pics": [("notifications", "The Notifications page")],
        "tip": "The portal message is the official record. The email is only a copy.",
    },
    # Part 4
    {
        "part": 4,
        "title": "See what needs your action",
        "role": "dbgi",
        "steps": [
            "Sign in and click **Administration** in the top menu.",
            "The dashboard lists deals to review and prices to decide.",
            "It also shows end-users to check, failed emails, and prices about to end.",
        ],
        "pics": [("dashboard", "The operations dashboard")],
    },
    {
        "part": 4,
        "title": "Start the review",
        "role": "dbgi",
        "steps": [
            "Open the deal.",
            "Read the **System recommendation**. It is only a hint. You decide.",
            "Check the details and the attachment.",
            "Type why you are starting in **Review reason**.",
            "Click **Start review**.",
        ],
        "pics": [("review-card", "The review box before the review starts")],
    },
    {
        "part": 4,
        "title": "Choose one of four decisions",
        "role": "dbgi",
        "table": [
            ["Choice", "Use it when"],
            ["Link to an existing opportunity", "The project is already in the portal"],
            ["Create a new whole opportunity", "This is the first deal for this project"],
            ["Request changes", "The partner must fix or add something"],
            ["Reject registration", "The deal cannot go on. Explain why."],
        ],
        "widths": [2, 3],
        "pics": [("options-card", "The four decisions")],
        "tip": "The partner can read your change instructions or rejection reason in Activity. Other reasons stay inside DBGI.",
    },
    # Part 5
    {
        "part": 5,
        "title": "DBGI asks for changes",
        "role": "dbgi",
        "steps": [
            "Choose **Request changes**.",
            "Say exactly what to fix in **Instructions for company**.",
            "Click **Request changes**.",
        ],
        "pics": [("changes-card", "Writing the instructions")],
    },
    {
        "part": 5,
        "title": "The partner reads what to fix",
        "role": "partner",
        "steps": [
            "You get a message. The status is now **Returned for changes**.",
            "Open the deal.",
            "Read DBGI's instructions under **Activity**.",
        ],
        "pics": [
            ("returned-top", "The deal is returned"),
            ("ret-activity", "DBGI's instructions in Activity"),
        ],
    },
    {
        "part": 5,
        "title": "The partner fixes it and saves",
        "role": "partner",
        "steps": [
            "Click **Edit registration**.",
            "Make the change.",
            "Click **Save changes**.",
            "The status becomes **Resubmitted** and DBGI checks it again.",
        ],
        "pics": [("edit-save", "Editing the attachment description")],
        "tip": "Your place in line does not change when you fix a returned deal.",
    },
    # Part 6
    {
        "part": 6,
        "title": "DBGI confirms the deal",
        "role": "dbgi",
        "steps": [
            "Start the review again.",
            "Choose **Create a new whole opportunity**, or link to an existing one.",
            "Type your reason in **Decision reason**.",
            "Click the button at the bottom of the box.",
        ],
        "pics": [("confirm-card", "Creating a new project for this deal")],
    },
    {
        "part": 6,
        "title": "The deal is now Registered",
        "role": "both",
        "intro": "The deal now belongs to a project, and it has a rank. The price is decided separately.",
        "pics": [("confirmed-top", "The Registered label and the project label")],
        "tip": (
            "Sometimes the portal does this by itself. It happens only when the end-user's name and address "
            "and all the products exactly match one project. The partner gets a message."
        ),
    },
    # Part 7
    {
        "part": 7,
        "title": "Open the price decision",
        "role": "dbgi",
        "steps": [
            "Click **Administration**.",
            "Click **Price approvals** in the left menu.",
            "Search for the deal and open it.",
        ],
        "pics": [("price-list", "The Price approvals list")],
    },
    {
        "part": 7,
        "title": "Approve the price",
        "role": "dbgi",
        "intro": "Rank 1 gets the best price. Everyone after rank 1 gets the same price. The form shows the rank and other prices.",
        "steps": [
            "Set **Status** to Approved.",
            "Type your reason in **Rationale**. The partner can read it.",
            "**Valid until**: choose the end date. If you leave it blank, the price lasts 90 days.",
            "Under **Registration item approvals**, click **Add another**.",
            "Choose the product and type the approved price.",
            "Click **Save**. A warning means the price breaks the rule. It still saves, so you can make an exception.",
        ],
        "pics": [
            ("price-form", "The top of the form: status, reason, and end date"),
            ("price-items", "The bottom of the form: the approved price for each product"),
        ],
        "warn": "Do not skip the approved price. If you do, the partner sees Pending instead of the price.",
    },
    # Part 8
    {
        "part": 8,
        "title": "The partner sees the price",
        "role": "partner",
        "steps": [
            "You get a message.",
            "**Commercial approvals** shows the decision, the end date, and the reason.",
            "**Requested products** shows the approved price for each product.",
        ],
        "pics": [
            ("app-approvals", "The approved price decision and its end date"),
            ("app-products", "The approved unit price"),
        ],
    },
    {
        "part": 8,
        "title": "Ask to renew a price",
        "role": "partner",
        "intro": "You get a reminder 14 days before the price ends. If you need more time, ask for a renewal.",
        "steps": [
            "Click **Request renewal** in **Commercial approvals**.",
            "Type your reason.",
            "Click **Send request**.",
            "The page shows **Waiting for DBGI** until DBGI answers.",
        ],
        "pics": [("renewal-request", "Asking for a renewal")],
        "tip": "You can send one request at a time. Please give DBGI at least one working day.",
    },
    {
        "part": 8,
        "title": "DBGI answers the renewal",
        "role": "dbgi",
        "steps": [
            "You get a message and an email.",
            "Open the deal. The partner's reason is in **Commercial approvals**.",
            "Click **Approve** or **Decline**, then type your reason.",
        ],
        "pics": [
            ("ren-approvals", "The renewal request on the deal page"),
            ("renewal-decide", "Approving the renewal"),
        ],
        "tip": (
            "Approving adds 30 days to the end date. If the price has already ended, the 30 days start today. "
            "Declining keeps the same date. The partner gets a message either way."
        ),
    },
    {
        "part": 8,
        "title": "See your rank",
        "role": "partner",
        "steps": [
            "Click **Rankings** in the top menu.",
            "**Rank** is your place on that project. The first to register gets rank 1.",
            "Rank 1 gets the best price. Everyone after rank 1 gets the same price.",
            "You see only your own rank, not the other companies.",
        ],
        "pics": [("rank-partner", "The Rankings page")],
        "tip": "**Tied** means another company registered at the very same time. DBGI will decide the order.",
    },
    # Part 9
    {
        "part": 9,
        "title": "How to change a deal",
        "role": "partner",
        "intro": "You can edit your deal any time until you withdraw it. Some parts lock during review.",
        "steps": [
            "Open the deal and click **Edit registration**.",
            "Make your change and click **Save changes**.",
            "Want today's list price? Tick the box at the top of the page. DBGI will check it.",
        ],
        "pics": [("edit-top", "The top of the edit page, with the list price box")],
        "warn": "If someone else saved first, the portal asks you to refresh. It will not overwrite their work.",
    },
    {
        "part": 9,
        "title": "Which changes does DBGI check?",
        "role": "partner",
        "table": [
            ["DBGI does not need to check", "DBGI must check"],
            [
                "Contact person, designation, email, and number",
                "End-user, project title, bid date, delivery date",
            ],
            [
                "Competitor remarks and product justifications",
                "Competitor brand, model, or bid price",
            ],
            [
                "Only capitals, punctuation, or spacing in the title or attachment description",
                "Products, quantities, or requested prices",
            ],
            ["", "Attachment description or link, and asking for today's list price"],
        ],
        "widths": [1, 1],
        "tip": "Your rank stays when DBGI checks a change. Every change is saved in Activity.",
    },
    {
        "part": 9,
        "title": "Does a change affect the price?",
        "role": "partner",
        "table": [
            ["What you change", "What happens to the list price"],
            ["Contact details, end-user, dates, or attachment", "It stays the same"],
            ["Quantity", "The unit price stays. The total is worked out again."],
            ["A product is added or changed", "Only that product takes today's list price"],
            ["You tick the box for today's price", "All catalog products take today's list price"],
        ],
        "widths": [1, 1],
        "warn": (
            "Once price review starts, products, quantities, and requested prices are locked. Ask DBGI to "
            "request changes first. Attachments are locked during review and after a decision."
        ),
    },
    # Part 10
    {
        "part": 10,
        "title": "Withdraw a deal",
        "role": "partner",
        "intro": "Do this if your company will not go on with the deal.",
        "steps": [
            "Open the deal and click **Withdraw registration**.",
            "Type your reason.",
            "Click **Withdraw registration** in the box.",
        ],
        "pics": [
            ("withdraw", "Confirming the withdrawal"),
            ("withdrawn-top", "The deal is now Withdrawn"),
        ],
        "warn": "This cannot be undone. The deal leaves the ranking. If the project comes back, register a new deal.",
    },
    # Part 11
    {
        "part": 11,
        "title": "Report if you won or lost",
        "role": "partner",
        "intro": "You can do this once DBGI has linked your deal to a project.",
        "steps": [
            "Click **Report project outcome**.",
            "Choose **Won**, **Lost**, or **Cancelled**.",
            "Say what happened, like the notice of award you received.",
            "Click **Send report**.",
        ],
        "pics": [
            ("outcome", "Reporting the result"),
            ("out-partner", "Your report waits for DBGI"),
        ],
        "tip": "If DBGI does not accept your report, you can read the note and report again.",
    },
    {
        "part": 11,
        "title": "DBGI checks the report",
        "role": "dbgi",
        "steps": [
            "You get a message and an email.",
            "Open the deal and find **Project outcome reports**.",
            "Click **Confirm** or **Do not accept**, and add a note.",
        ],
        "pics": [("out-dbgi", "The report waiting for your decision")],
        "tip": "Confirming changes the project's status for every deal linked to it. The partner gets a message.",
    },
    # Part 12
    {
        "part": 12,
        "title": "The time limits",
        "role": "both",
        "table": [
            ["What", "Limit", "What happens"],
            [
                "A deal DBGI has not confirmed",
                "60 days",
                "Reminder on day 53. On day 60 it goes back to DBGI's review list. It is never rejected by itself.",
            ],
            [
                "A project on hold",
                "60 days",
                "Reminder on day 53. On day 60 the deals go back to DBGI for review.",
            ],
            [
                "An approved price",
                "90 days if DBGI sets no date",
                "Reminder 14 days before it ends. After that it shows as Expired.",
            ],
            [
                "A renewed price",
                "30 more days",
                "Added to the end date, or counted from today if the price has ended.",
            ],
        ],
        "widths": [3, 2, 6],
        "tip": "We count every calendar day, in Philippine time. Reminders start once IT turns on the portal's daily job.",
    },
    {
        "part": 12,
        "title": "Put a project on hold",
        "role": "dbgi",
        "intro": "Use this when a tender is postponed or will be posted again.",
        "steps": [
            "Click **Administration**, then **Opportunities**.",
            "Open the project.",
            "Set **Project status** to On hold.",
            "Click **Save**.",
        ],
        "pics": [("project-status", "The project form")],
        "tip": "Deals keep their place for 60 days. Any other status ends the hold. A new hold starts a new 60 days.",
    },
    # Part 13
    {
        "part": 13,
        "title": "Change a list price",
        "role": "dbgi",
        "steps": [
            "Click **Administration**, then **Products**, and open the product.",
            "Under **Product prices**, click **Add another Product price**.",
            "Type the price, the start date, and the reason.",
            "Click **Save**.",
        ],
        "pics": [("price-add", "A product and its price history")],
        "tip": "Old prices are never changed or deleted. A start date in the future schedules the change.",
    },
    {
        "part": 13,
        "title": "Apply today's prices to a deal",
        "role": "dbgi",
        "steps": [
            "Open the deal and click **Apply current list prices**.",
            "Type your reason.",
            "Click **Apply prices**.",
        ],
        "pics": [("reprice", "Applying today's list prices")],
        "tip": "You can do this until price review starts. The partner gets a message and can read your reason.",
    },
    {
        "part": 13,
        "title": "Add a product to the catalog",
        "role": "dbgi",
        "intro": "A product marked Not in catalog gets no price review until you do this.",
        "steps": [
            "Open the deal and click **Add to catalog** on the product.",
            "Choose **New product** or **Existing product**.",
            "Fill in the details and your reason.",
            "Click **Add to catalog**.",
        ],
        "pics": [("catalog", "Adding the product")],
        "tip": "The product now has a list price, and its price review opens. The partner gets a message.",
    },
    {
        "part": 13,
        "title": "Decide a tie",
        "role": "dbgi",
        "intro": "A tie means two companies registered at the very same time.",
        "steps": [
            "Click **Rankings**, then **Decide tie**.",
            "Use the arrows to put the companies in order.",
            "Type your reason, then click **Save order**.",
        ],
        "pics": [("rank-dbgi", "DBGI sees every company"), ("tie", "Setting the order")],
        "tip": "Companies see only their new rank, not your reason.",
    },
    {
        "part": 13,
        "title": "Merge two projects",
        "role": "dbgi",
        "intro": "Use this when you learn that two projects are the same tender.",
        "steps": [
            "Click **Rankings**, then **Merge** on the project to close.",
            "In **Merge into**, choose the project to keep.",
            "Check the new ranking. The earliest deal comes first.",
            "Choose what happens to decided prices.",
            "Type your reason, then click **Merge projects**.",
        ],
        "pics": [("merge-dialog", "The new ranking before you merge")],
        "warn": "This cannot be undone. Companies get a message, but only DBGI can read your reason.",
    },
    {
        "part": 13,
        "title": "Split a deal",
        "role": "dbgi",
        "intro": "Use this when one deal covers separate lots.",
        "steps": [
            "Open the deal and click **Split deal**.",
            "Tick the products to move. At least one must stay.",
            "Type a new lot name, or choose an existing lot.",
            "Choose what happens to decided prices.",
            "Type your reason, then click **Split deal**.",
        ],
        "pics": [("split-dialog", "Moving a product to a new lot")],
        "tip": "The new deal keeps the same company and the original submission time.",
    },
    {
        "part": 13,
        "title": "Keep the public holiday list",
        "role": "dbgi",
        "intro": "The portal needs this list to count working days.",
        "steps": [
            "Click **Administration**, then **Public holidays**.",
            "Click the add button.",
            "Type the date and the name of the holiday.",
            "Click **Save**.",
        ],
        "tip": "A working day is Monday to Friday, without public holidays. After 5:00 PM, counting starts on the next working day.",
    },
    # Part 14
    {
        "part": 14,
        "title": "What is a repeat order?",
        "role": "both",
        "intro": "The same buyer orders more of the same item, without a new bidding.",
        "table": [
            ["The rule", "What it means"],
            ["Same end-user", "The order must come from the same office as the original deal"],
            [
                "Notice of Award (NOA)",
                "The buyer's letter saying you won. It must say repeat order.",
            ],
            [
                "Notice to Proceed (NTP)",
                "The buyer's letter saying go ahead. It must say repeat order.",
            ],
            ["A valid approved price", "If the price has ended, renew it first"],
        ],
        "widths": [2, 3],
        "tip": "If any of these is missing, DBGI declines it. You can register a new deal instead.",
    },
    {
        "part": 14,
        "title": "Ask for a repeat order",
        "role": "partner",
        "steps": [
            "Open the deal and click **Request repeat order**.",
            "Type the quantity for each product.",
            "Add both letters, the NOA and the NTP.",
            "Tick the box to confirm what the letters say.",
            "Click **Send request**.",
        ],
        "pics": [("repeat-request", "Asking for a repeat order")],
        "tip": "Please give DBGI at least one working day.",
    },
    {
        "part": 14,
        "title": "DBGI decides the repeat order",
        "role": "dbgi",
        "steps": [
            "Open the deal and find **Repeat orders**.",
            "Click **NOA** and **NTP** to read the letters.",
            "Click **Accept** or **Decline**, then type your reason.",
        ],
        "pics": [
            ("repeat-decide", "Accepting the repeat order"),
            ("repeat-section", "What the partner sees afterward"),
        ],
        "tip": "The partner gets a message and can read your reason.",
    },
    # Part 15
    {
        "part": 15,
        "title": "Five things to remember",
        "role": None,
        "bullets": [
            "**Register early.** The first to register gets rank 1, and rank 1 gets the best price.",
            "**A requested price is not an approved price.** Wait for DBGI.",
            "**Read Activity.** DBGI's reasons and instructions are there.",
            "**Do not upload private papers** or other companies' prices.",
            "**Withdrawing is final.** You would need to register a new deal.",
        ],
    },
    {
        "part": 15,
        "title": "I want to...",
        "role": None,
        "table": [
            ["I want to...", "Go to"],
            ["Add a deal", "Deal list, then New registration"],
            ["Fix or change a deal", "Open the deal, then Edit registration"],
            ["See DBGI's reason", "Open the deal, then Activity"],
            ["See my approved price", "Open the deal, then Commercial approvals"],
            ["Make my price last longer", "Commercial approvals, then Request renewal"],
            ["See my place on a project", "Rankings"],
            ["Use my approved price again", "Open the deal, then Request repeat order"],
            ["Tell DBGI I won or lost", "Open the deal, then Report project outcome"],
            ["Stop a deal", "Open the deal, then Withdraw registration"],
        ],
        "widths": [2, 3],
    },
    {
        "part": 15,
        "title": "Word list",
        "role": None,
        "table": [
            ["Word on the screen", "What it means"],
            ["End-user", "The government office that will buy"],
            ["Opportunity", "The project that companies are bidding for"],
            ["Whole opportunity (scope)", "The whole project, not just one lot of it"],
            ["Competitor item", "The other brand's product and its price"],
            ["Attachment", "Your proof, like a request for quotation"],
            ["List price", "DBGI's normal price, with VAT"],
            ["Requested unit price", "The price you ask for, for one piece"],
            ["Approved unit price", "The price DBGI agreed to, for one piece"],
            ["Commercial approvals", "DBGI's price decisions"],
            ["Rationale", "The reason for a decision"],
            ["Renewal", "Asking DBGI to make a price last longer"],
            ["Repeat order", "The same buyer orders more, without a new bidding"],
            ["NOA and NTP", "The buyer's letters: Notice of Award, Notice to Proceed"],
        ],
        "widths": [2, 3],
    },
]
