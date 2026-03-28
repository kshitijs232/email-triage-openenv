"""
Email Triage Environment - Sample Email Datasets

Contains email data for different task difficulty levels.
"""

# Handle both relative and absolute imports
try:
    from ..models import Email, EmailCategory, EmailPriority, EmailActionType
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from models import Email, EmailCategory, EmailPriority, EmailActionType

# =============================================================================
# EASY TASK - 3 emails with clear categories
# =============================================================================
EASY_EMAILS = [
    Email(
        id="easy_001",
        sender="winner-notification@lottery-scam.com",
        subject="🎉 CONGRATULATIONS! You Won $1,000,000!!!",
        body="""Dear Lucky Winner,

You have been selected to receive ONE MILLION DOLLARS!

Click here immediately to claim your prize: http://totally-legit.scam/claim

You must act within 24 hours or forfeit your winnings!

Send us your bank details and SSN to process the transfer.

Best regards,
The Totally Real Lottery Commission""",
        timestamp="2024-01-15 09:23:00",
        correct_category=EmailCategory.SPAM,
        correct_priority=EmailPriority.LOW,
        correct_action=EmailActionType.DELETE,
        requires_response=False,
    ),
    Email(
        id="easy_002",
        sender="sarah.chen@company.com",
        subject="Q4 Budget Review Meeting - Action Required",
        body="""Hi,

Please review the attached Q4 budget proposal before our meeting tomorrow at 2pm.

Key items to discuss:
1. Marketing spend increase (+15%)
2. Engineering headcount request
3. Office renovation budget

Let me know if you have any questions.

Thanks,
Sarah
Finance Director""",
        timestamp="2024-01-15 10:45:00",
        correct_category=EmailCategory.WORK,
        correct_priority=EmailPriority.HIGH,
        correct_action=EmailActionType.RESPOND,
        requires_response=True,
    ),
    Email(
        id="easy_003",
        sender="mom@family.com",
        subject="Grandma's birthday next Sunday",
        body="""Hi sweetie,

Just a reminder that Grandma's 80th birthday party is next Sunday at 3pm.

Can you bring the cake? Let me know what flavor you're thinking.

Love you!
Mom""",
        timestamp="2024-01-15 11:30:00",
        correct_category=EmailCategory.PERSONAL,
        correct_priority=EmailPriority.MEDIUM,
        correct_action=EmailActionType.RESPOND,
        requires_response=True,
    ),
]

# =============================================================================
# MEDIUM TASK - 5 emails with some ambiguity
# =============================================================================
MEDIUM_EMAILS = [
    Email(
        id="med_001",
        sender="newsletter@techcrunch.com",
        subject="This week in AI: GPT-5 rumors, Apple's new chip",
        body="""TechCrunch Weekly Digest

TOP STORIES:
- GPT-5 reportedly in testing at OpenAI
- Apple announces M4 Ultra chip
- Startup raises $500M for quantum computing

Read more at techcrunch.com

Unsubscribe: click here""",
        timestamp="2024-01-15 08:00:00",
        correct_category=EmailCategory.NEWSLETTER,
        correct_priority=EmailPriority.LOW,
        correct_action=EmailActionType.ARCHIVE,
        requires_response=False,
    ),
    Email(
        id="med_002",
        sender="ceo@company.com",
        subject="URGENT: Client meeting moved to TODAY",
        body="""Everyone,

The BigCorp client meeting has been moved from Friday to TODAY at 4pm.

This is our biggest account. All hands on deck.

Be prepared to present Q4 results and 2025 roadmap.

Room: Conference A
Dial-in: 555-0123

- CEO""",
        timestamp="2024-01-15 13:00:00",
        correct_category=EmailCategory.URGENT,
        correct_priority=EmailPriority.CRITICAL,
        correct_action=EmailActionType.FLAG,
        requires_response=False,
    ),
    Email(
        id="med_003",
        sender="support@amazon.com",
        subject="Your order has shipped!",
        body="""Hello,

Great news! Your order #123-456-789 has shipped.

Items: USB-C Cable (2-pack)
Estimated delivery: January 17, 2024

Track your package: amazon.com/track

Thanks for shopping with us!
Amazon Customer Service""",
        timestamp="2024-01-15 14:22:00",
        correct_category=EmailCategory.PERSONAL,
        correct_priority=EmailPriority.LOW,
        correct_action=EmailActionType.ARCHIVE,
        requires_response=False,
    ),
    Email(
        id="med_004",
        sender="hr@company.com",
        subject="Benefits enrollment deadline reminder",
        body="""Hi team,

This is a reminder that open enrollment for 2024 benefits ends THIS FRIDAY.

If you haven't made your selections yet, please log into the benefits portal
and complete your enrollment.

Changes include:
- New dental provider options
- Increased 401k match (up to 6%)
- New mental health benefits

Questions? Contact HR at hr@company.com

Thanks,
HR Team""",
        timestamp="2024-01-15 09:00:00",
        correct_category=EmailCategory.WORK,
        correct_priority=EmailPriority.HIGH,
        correct_action=EmailActionType.FLAG,
        requires_response=False,
    ),
    Email(
        id="med_005",
        sender="prince.nigeria@gmail.com",
        subject="Business Proposal - Confidential",
        body="""Dear Friend,

I am Prince Adeleke from Nigeria. My late father left $45,000,000 
in a bank account that I need help transferring.

If you assist me, I will give you 30% of the funds.

Please reply with your bank account details to proceed.

God bless you,
Prince Adeleke""",
        timestamp="2024-01-15 03:45:00",
        correct_category=EmailCategory.SPAM,
        correct_priority=EmailPriority.LOW,
        correct_action=EmailActionType.DELETE,
        requires_response=False,
    ),
]

# =============================================================================
# HARD TASK - 10 emails with complex scenarios
# =============================================================================
HARD_EMAILS = [
    Email(
        id="hard_001",
        sender="security@paypa1.com",  # Note: paypa1 not paypal
        subject="Unusual activity detected on your account",
        body="""PayPal Security Alert

We detected unusual signin activity on your account.

Location: Moscow, Russia
Time: 3:45 AM EST

If this wasn't you, verify your account immediately:
http://paypa1-secure.com/verify

PayPal Security Team""",
        timestamp="2024-01-15 03:45:00",
        correct_category=EmailCategory.SPAM,  # Phishing attempt
        correct_priority=EmailPriority.LOW,
        correct_action=EmailActionType.DELETE,
        requires_response=False,
    ),
    Email(
        id="hard_002",
        sender="john.smith@bigcorp-client.com",
        subject="RE: RE: RE: Contract renewal discussion",
        body="""Thanks for the updated proposal.

One issue: Section 3.2 still shows the old pricing. We agreed on 
15% discount for the 3-year term.

Can you send a corrected version by EOD? Our legal team is waiting 
to review.

Also, are we still on for golf Saturday?

John""",
        timestamp="2024-01-15 16:30:00",
        correct_category=EmailCategory.URGENT,  # Client + deadline
        correct_priority=EmailPriority.CRITICAL,
        correct_action=EmailActionType.RESPOND,
        requires_response=True,
    ),
    Email(
        id="hard_003",
        sender="linkedin@linkedin.com",
        subject="You have 15 new connection requests",
        body="""LinkedIn

You're popular this week!

15 people want to connect:
- John D., Recruiter at Tech Giant
- Sarah M., Product Manager
- Mike R., CEO at Startup Inc.
... and 12 more

See all requests: linkedin.com/mynetwork

---
You can unsubscribe from these emails in your settings.""",
        timestamp="2024-01-15 10:00:00",
        correct_category=EmailCategory.NEWSLETTER,
        correct_priority=EmailPriority.LOW,
        correct_action=EmailActionType.ARCHIVE,
        requires_response=False,
    ),
    Email(
        id="hard_004",
        sender="alice.wong@company.com",
        subject="Fwd: Customer complaint - needs immediate attention",
        body="""Hey,

Can you handle this? I'm out sick today.

The customer below is threatening to churn. They're a $500k/year account.

---------- Forwarded message ---------
From: angry.customer@bigcompany.com
Subject: This is unacceptable

We've been waiting 3 weeks for support on our integration issue.
If this isn't resolved by Friday, we're switching to your competitor.

This is your last chance.""",
        timestamp="2024-01-15 11:15:00",
        correct_category=EmailCategory.URGENT,
        correct_priority=EmailPriority.CRITICAL,
        correct_action=EmailActionType.RESPOND,
        requires_response=True,
    ),
    Email(
        id="hard_005",
        sender="old-friend@protonmail.com",
        subject="Long time no talk",
        body="""Hey!

Remember me? We went to college together! It's been 15 years!

I saw your profile on LinkedIn and wanted to reconnect. I'm actually
in your city next month for a conference.

Want to grab coffee and catch up? Would love to hear what you've 
been up to.

- Your old roommate (hint: I was the one who almost burned down
  the dorm making ramen)""",
        timestamp="2024-01-15 19:30:00",
        correct_category=EmailCategory.PERSONAL,
        correct_priority=EmailPriority.MEDIUM,
        correct_action=EmailActionType.RESPOND,
        requires_response=True,
    ),
    Email(
        id="hard_006",
        sender="it-department@company.com",
        subject="Mandatory: Password reset required",
        body="""IT Security Notice

As part of our quarterly security audit, all employees must reset 
their passwords by Friday.

New requirements:
- Minimum 16 characters
- Must include number and special character
- Cannot reuse last 10 passwords

Reset here: https://company-internal.okta.com/reset

This is a legitimate IT request - you can verify by calling the 
IT helpdesk at ext. 5555.

IT Security Team""",
        timestamp="2024-01-15 09:00:00",
        correct_category=EmailCategory.WORK,
        correct_priority=EmailPriority.HIGH,
        correct_action=EmailActionType.FLAG,
        requires_response=False,
    ),
    Email(
        id="hard_007",
        sender="deals@store.com",
        subject="Flash Sale: 70% off everything!",
        body="""🔥 24-HOUR FLASH SALE 🔥

Everything must go!

Use code FLASH70 for 70% off your entire order!

Shop now: store.com/sale

Free shipping on orders over $50!

---
You're receiving this because you signed up for our mailing list.
Unsubscribe: store.com/unsubscribe""",
        timestamp="2024-01-15 07:00:00",
        correct_category=EmailCategory.NEWSLETTER,  # Promotional
        correct_priority=EmailPriority.LOW,
        correct_action=EmailActionType.DELETE,  # User didn't sign up
        requires_response=False,
    ),
    Email(
        id="hard_008",
        sender="boss@company.com",
        subject="Private: Your performance review",
        body="""Hi,

I wanted to give you a heads up before our formal review next week.

Overall, you've done great work this year. I'm recommending you 
for promotion to Senior level.

However, I do want to discuss a few areas for growth:
- Cross-team collaboration
- Presentation skills

Can you block 30 min on my calendar this week to discuss?

- Your Manager""",
        timestamp="2024-01-15 17:00:00",
        correct_category=EmailCategory.WORK,
        correct_priority=EmailPriority.HIGH,
        correct_action=EmailActionType.RESPOND,
        requires_response=True,
    ),
    Email(
        id="hard_009",
        sender="bank-alerts@chase.com",
        subject="Fraud Alert: Suspicious transaction",
        body="""Chase Fraud Protection

We detected a potentially unauthorized transaction:

Amount: $1,247.00
Merchant: ELECTRONICS STORE MOSCOW RU
Date: January 15, 2024

Was this you?

If YES: No action needed
If NO: Call us immediately at 1-800-935-9935

This number is on the back of your Chase card.

Chase Fraud Department""",
        timestamp="2024-01-15 14:00:00",
        correct_category=EmailCategory.URGENT,  # Legitimate bank alert
        correct_priority=EmailPriority.CRITICAL,
        correct_action=EmailActionType.FLAG,
        requires_response=False,  # Call, don't email
    ),
    Email(
        id="hard_010",
        sender="charity@savethechildren.org",
        subject="Thank you for your donation",
        body="""Dear Supporter,

Thank you for your generous donation of $50 to Save the Children.

Your contribution will help provide:
- Clean water for 5 children for a month
- School supplies for 2 students
- Emergency food supplies

Your tax receipt is attached.

With gratitude,
Save the Children Foundation

---
Manage your giving: savethechildren.org/account""",
        timestamp="2024-01-15 12:00:00",
        correct_category=EmailCategory.PERSONAL,
        correct_priority=EmailPriority.LOW,
        correct_action=EmailActionType.ARCHIVE,
        requires_response=False,
    ),
]


# Task registry
TASK_EMAILS = {
    "easy": EASY_EMAILS,
    "medium": MEDIUM_EMAILS,
    "hard": HARD_EMAILS,
}

TASK_DESCRIPTIONS = {
    "easy": "3 emails with clear categories (spam, work, personal)",
    "medium": "5 emails with some ambiguity in priority",
    "hard": "10 emails with phishing, urgent chains, and edge cases",
}
