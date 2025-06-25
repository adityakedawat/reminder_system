import os
import logging
import requests
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from .db import DBAdapter
from enum import Enum
from jinja2 import Template

class ReceiverType(Enum):
    individual = "individual"
    group = "group"


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EmailTemplate:
    subject: str
    body: str
    name: str
    external_reference_info: str
    data_references: List[str]
    template_id: int

@dataclass
class Client:
    first_name: str
    last_name: str
    middle_name: str
    company_name: str
    company_type: str
    email: str
    mobile: int
    gst_no: str
    address: str
    id: int

@dataclass
class ReminderData:
    reminder_id: int
    reminder_type_id: int
    deadline: date
    days_before_deadline: List[int]
    reminder_type_name: str
    receivers: List[Client]
    email_template: EmailTemplate


class MailerSendService:
    def __init__(self):
        self.api_key = os.getenv("MAILERSEND_API_KEY")
        self.from_email = os.getenv("MAILERSEND_FROM_EMAIL")
        self.from_name = os.getenv("MAILERSEND_FROM_NAME", "Reminder System")
        self.base_url = "https://api.mailersend.com/v1"

        if not self.api_key:
            raise ValueError("MAILERSEND_API_KEY environment variable is required")
        if not self.from_email:
            raise ValueError("MAILERSEND_FROM_EMAIL environment variable is required")

    def send_email(
        self, to_email: str, to_name: str, subject: str, body: str
    ) -> Dict[str, Any]:
        """Send email using MailerSend API"""
        url = f"{self.base_url}/email"

        payload = {
            "from": {"email": self.from_email, "name": self.from_name},
            "to": [{"email": to_email, "name": to_name}],
            "subject": subject,
            "html": body,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return {"success": True, "message_id": response.headers.get("x-message-id")}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return {"success": False, "error": str(e)}


class ReminderService:
    def __init__(self):
        self.db = DBAdapter()
        self.mailer = MailerSendService()

    def get_todays_reminders(self) -> List[ReminderData]:
        """Get all reminders that should be sent today"""
        today = date.today()

        try:
            result = (
                self.db.client.table("reminder_info")
                .select(
                    "reminder_type_id,deadline,days_before_deadline,receiver_id,receiver_type,reminder_id"
                )
                .gte("deadline", today)
                .execute()
            )
            # For now, we'll use a simpler approach and filter in Python
            # In production, you might want to use raw SQL queries

            reminders = []
            for row in result.data:
                # Calculate days until deadline
                days_until_deadline = (date.fromisoformat(row["deadline"]) - today).days

                # Check if today is one of the reminder days
                if days_until_deadline in row["days_before_deadline"]:
                    # Get group info
                    if row["receiver_type"] == ReceiverType.group.value:
                        client_ids_result = (
                            self.db.client.table("client_group_map")
                            .select("client_id")
                            .eq("group_id", row["receiver_id"])
                            .execute()
                        )
                        client_ids = [item["client_id"] for item in client_ids_result.data]
                    else:
                        client_ids = [row["receiver_id"]]

                    clients_dict = (
                        self.db.client.table("clients")
                        .select(
                            "id,first_name,last_name,middle_name,company_name,company_type,email,mobile,gst_no,address"
                        )
                        .in_("id", client_ids)
                        .execute()
                    ).data
                    clients = [Client(**client_dict) for client_dict in clients_dict]
                    # Get reminder type and template info
                    reminder_type_result = (
                        self.db.client.table("reminder_type_info")
                        .select("email_template_id,name")
                        .eq("reminder_type_id", row["reminder_type_id"])
                        .execute()
                    )
                    if not reminder_type_result.data:
                        continue

                    reminder_type_dict = reminder_type_result.data[0]
                    reminder_type_dict["reminder_type_name"] = reminder_type_dict.pop("name")
                    template_result = (
                        self.db.client.table("email_template")
                        .select("subject,body,external_reference_info,name,data_references,template_id")
                        .eq("template_id", reminder_type_dict["email_template_id"])
                        .execute()
                    )
                    if not template_result.data:
                        continue

                    template = EmailTemplate(**template_result.data[0])
                    row.pop("receiver_type")
                    row.pop("receiver_id")
                    reminder_type_dict.pop("email_template_id")
                    reminder_data = ReminderData(
                        **row,
                        receivers=clients,
                        email_template=template,
                        **reminder_type_dict

                    )
                    reminders.append(reminder_data)

            return reminders

        except Exception as e:
            logger.error(f"Error fetching reminders: {str(e)}")
            return []

    def is_client_blocklisted(self, client_id: int) -> bool:
        """Check if client is in blocklist"""
        try:
            result = (
                self.db.client.table("reminder_blocklist")
                .select("*")
                .eq("client_id", client_id)
                .execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error checking blocklist for client {client_id}: {str(e)}")
            return False

    def is_reminder_already_sent(
        self,
        client_id: int,
        reminder_id: int,
        days_before_deadline: list[int],
        days_until_deadline: int,
    ):
        """Check if reminder stage >= last stage of reminder sent to the client"""
        try:
            reminder_stage = days_before_deadline.index(days_until_deadline)

            last_stage = len(
                self.db.client.table("reminder_status")
                .select("*")
                .eq("reminder_id", reminder_id)
                .eq("client_id", client_id)
                .eq("status","sent")
                .execute()
            ).data
            if reminder_stage >= last_stage:
                return False
            return True
        except Exception as e:
            logger.error(
                f"Error checking reminder status for client {client_id}: {str(e)}"
            )
            return False

    def is_client_unsubscribed(self, client_id: int, reminder_id: int) -> bool:
        """Check if client has unsubscribed from this specific reminder"""
        try:
            result = (
                self.db.client.table("reminder_unsubscribers")
                .select("*")
                .eq("client_id", client_id)
                .eq("reminder_id", reminder_id)
                .execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(
                f"Error checking unsubscribe for client {client_id}, reminder {reminder_id}: {str(e)}"
            )
            return False

    def update_reminder_status(
        self, reminder_id: int, client_id: int, status: str, error_message: str = None
    ):
        """Update reminder status in database"""
        try:
            status_data = {
                "reminder_id": reminder_id,
                "client_id": client_id,
                "status": status,
                "error_message": error_message,
            }

            self.db.client.table("reminder_status").insert(status_data).execute()
            logger.info(
                f"Updated status for reminder {reminder_id}, client {client_id}: {status}"
            )

        except Exception as e:
            logger.error(f"Error updating reminder status: {str(e)}")

    def process_reminders(self):
        """Main method to process all reminders for today"""
        logger.info("Starting reminder processing...")

        reminders = self.get_todays_reminders()
        logger.info(f"Found {len(reminders)} reminders to process. {reminders=}")

        success_count = 0
        error_count = 0

        for reminder in reminders:
            for client in reminder.receivers:
                try:
                    # Check if client has email
                    if not client.email:
                        self.update_reminder_status(
                            reminder.reminder_id,
                            client.id,
                            "error",
                            "No email address",
                        )
                        error_count += 1
                        continue

                    # Check blocklist
                    if self.is_client_blocklisted(client.id):
                        self.update_reminder_status(
                            reminder.reminder_id,
                            client.id,
                            "blocked",
                            "Client in blocklist",
                        )
                        logger.info(f"Client {client.id} is blocklisted, skipping")
                        continue

                    # Check unsubscribe
                    if self.is_client_unsubscribed(
                        client.id, reminder.reminder_id
                    ):
                        self.update_reminder_status(
                            reminder.reminder_id,
                            client.id,
                            "unsubscribed",
                            "Client unsubscribed",
                        )
                        logger.info(
                            f"Client {client.id} unsubscribed from reminder {reminder.reminder_id}"
                        )
                        continue

                    # Personalize email content
                    personalized_email = self._personalize_content(
                        reminder, client
                    )
                    

                    # Send email
                    result = self.mailer.send_email(
                        to_email=client.email,
                        to_name=f"{client.first_name} {client.middle_name} {client.last_name}",
                        subject=personalized_email["subject"],
                        body=personalized_email["body"],
                    )

                    if result["success"]:
                        self.update_reminder_status(
                            reminder.reminder_id, client.id, "sent"
                        )
                        success_count += 1
                        logger.info(
                            f"Successfully sent reminder {reminder.reminder_type_name} to {client.email}"
                        )
                    else:
                        self.update_reminder_status(
                            reminder.reminder_id,
                            client.id,
                            "error",
                            result.get("error", "Unknown error"),
                        )
                        error_count += 1
                        logger.error(
                            f"Failed to send reminder {reminder.reminder_type_name} to {client.email}"
                        )

                except Exception as e:
                    self.update_reminder_status(
                        reminder.reminder_id, client.id, "error", str(e)
                    )
                    error_count += 1
                    logger.error(
                        f"Error processing reminder {reminder.reminder_type_name}: {str(e)}"
                    )

        logger.info(
            f"Reminder processing completed. Success: {success_count}, Errors: {error_count}"
        )
        return success_count, error_count

    def _personalize_content(self, reminder: ReminderData, client: Client) -> str:
        """Personalize email content with client and reminder data"""
        references = {}
        references.update(asdict(reminder))
        references.update(asdict(client))
        references["days_until_deadline"] = str((date.fromisoformat(reminder.deadline) - date.today()).days)
        personalized_body = Template(reminder.email_template.body).render(references)
        personalized_subject = Template(reminder.email_template.subject).render(references)

        return {"body": personalized_body, "subject":personalized_subject}
