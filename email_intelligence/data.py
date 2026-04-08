from __future__ import annotations

from email_intelligence.models import EmailMessage


def load_sample_emails() -> list[EmailMessage]:
    return [
        EmailMessage(
            email_id="sample-001",
            sender="anita.sharma@clientops.com",
            subject="Revised contract needs approval before 4 PM",
            body=(
                "Hi team, the client has accepted the final revisions. "
                "Please review the attached contract and send approval before 4 PM today "
                "so legal can release it."
            ),
            received_at="2026-04-07 09:15",
            expected_category="Work",
            expected_action="Urgent Action",
        ),
        EmailMessage(
            email_id="sample-002",
            sender="winner@global-crypto-airdrop.biz",
            subject="Congratulations!!! Claim your instant crypto reward now",
            body=(
                "You have been selected for a limited-time bonus. Click now to verify your wallet, "
                "unlock your winnings, and claim your reward before the offer expires."
            ),
            received_at="2026-04-07 09:42",
            expected_category="Spam",
            expected_action="Ignore",
        ),
        EmailMessage(
            email_id="sample-003",
            sender="rahul.mehta@familymail.com",
            subject="Dinner at my place this Friday?",
            body=(
                "Hey, are you free for dinner this Friday evening? Let me know if you want me "
                "to book dessert from your favorite cafe."
            ),
            received_at="2026-04-07 10:05",
            expected_category="Personal",
            expected_action="Respond",
        ),
        EmailMessage(
            email_id="sample-004",
            sender="security-alerts@cloudstack.io",
            subject="Unusual login attempt detected on finance workspace",
            body=(
                "We detected a login from an unrecognized device on the finance workspace at 08:57 AM. "
                "Review activity immediately and rotate credentials if this was not you."
            ),
            received_at="2026-04-07 10:18",
            expected_category="Work",
            expected_action="Urgent Action",
        ),
        EmailMessage(
            email_id="sample-005",
            sender="newsletter@shopmax.example",
            subject="Flash sale on luxury watches ends tonight",
            body=(
                "Browse our premium collection with up to 70 percent off. Limited inventory. "
                "Act now and enjoy exclusive VIP pricing."
            ),
            received_at="2026-04-07 10:31",
            expected_category="Spam",
            expected_action="Ignore",
        ),
        EmailMessage(
            email_id="sample-006",
            sender="meera.narayan@startuphub.ai",
            subject="Can you review the investor update draft before 3 PM?",
            body=(
                "I have drafted the investor update for this month. When you get a chance today, "
                "please review the metrics section and suggest any edits before I send it out."
            ),
            received_at="2026-04-07 11:02",
            expected_category="Work",
            expected_action="Respond",
        ),
        EmailMessage(
            email_id="sample-007",
            sender="bookings@holidayescape.travel",
            subject="Confirm your beach villa reservation in the next 30 minutes",
            body=(
                "Your reservation is waiting, but you must confirm immediately to avoid cancellation. "
                "Submit payment details right away to lock in your package."
            ),
            received_at="2026-04-07 11:26",
            expected_category="Spam",
            expected_action="Ignore",
        ),
        EmailMessage(
            email_id="sample-008",
            sender="mom@familymail.com",
            subject="Doctor meeting at 10 AM tomorrow",
            body=(
                "Please check the reports when I send them later today and tell me if you can join "
                "the doctor's call tomorrow morning. The meeting is at 10 AM."
            ),
            received_at="2026-04-07 11:44",
            expected_category="Personal",
            expected_action="Respond",
        ),
        EmailMessage(
            email_id="sample-009",
            sender="ops@northbridge-logistics.com",
            subject="Shipment delay may impact tomorrow's launch",
            body=(
                "The primary hardware shipment is delayed by 12 hours due to weather. "
                "We need a mitigation decision before EOD so the launch schedule can be updated."
            ),
            received_at="2026-04-07 12:09",
            expected_category="Work",
            expected_action="Urgent Action",
        ),
        EmailMessage(
            email_id="sample-010",
            sender="college.friends@lists.social",
            subject="Photos from the reunion are finally ready",
            body=(
                "Uploading the reunion photos tonight. Reply if you want the shared drive link "
                "or if you want me to print a few copies."
            ),
            received_at="2026-04-07 12:31",
            expected_category="Personal",
            expected_action="Respond",
        ),
    ]
