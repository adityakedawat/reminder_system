import os
import logging
import requests
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from .db import DBAdapter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ReminderData:
    reminder_id: int
    client_id: int
    group_id: Optional[int]
    reminder_type_id: int
    deadline: date
    days_before_deadline: List[int]
    client_email: str
    client_name: str
    template_subject: str
    template_body: str
    template_name: str
    reminder_type_name: str


class MailerSendService:
    def __init__(self):
        self.api_key = os.getenv('MAILERSEND_API_KEY')
        self.from_email = os.getenv('MAILERSEND_FROM_EMAIL')
        self.from_name = os.getenv('MAILERSEND_FROM_NAME', 'Reminder System')
        self.base_url = 'https://api.mailersend.com/v1'
        
        if not self.api_key:
            raise ValueError("MAILERSEND_API_KEY environment variable is required")
        if not self.from_email:
            raise ValueError("MAILERSEND_FROM_EMAIL environment variable is required")
    
    def send_email(self, to_email: str, to_name: str, subject: str, body: str) -> Dict[str, Any]:
        """Send email using MailerSend API"""
        url = f"{self.base_url}/email"
        
        payload = {
            "from": {
                "email": self.from_email,
                "name": self.from_name
            },
            "to": [
                {
                    "email": to_email,
                    "name": to_name
                }
            ],
            "subject": subject,
            "html": body
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return {"success": True, "message_id": response.json().get("message_id")}
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
        
        # Query to get reminders that need to be sent today
        query = """
        SELECT 
            ri.reminder_id,
            ri.client_id,
            ri.group_id,
            ri.reminder_type_id,
            ri.deadline,
            ri.days_before_deadline,
            c.email as client_email,
            COALESCE(c.first_name || ' ' || c.last_name, c.company_name) as client_name,
            et.subject as template_subject,
            et.body as template_body,
            et.name as template_name,
            rti.name as reminder_type_name
        FROM reminder_info ri
        JOIN reminder_type_info rti ON ri.reminder_type_id = rti.reminder_type_id
        JOIN email_template et ON rti.email_template_id = et.template_id
        LEFT JOIN clients c ON ri.client_id = c.id
        WHERE ri.deadline >= $1
        AND EXISTS (
            SELECT 1 FROM unnest(ri.days_before_deadline) AS day
            WHERE day = EXTRACT(DAY FROM (ri.deadline - $1))
        )
        """
        
        try:
            result = self.db.client.table('reminder_info').select('*').execute()
            # For now, we'll use a simpler approach and filter in Python
            # In production, you might want to use raw SQL queries
            
            reminders = []
            for row in result.data:
                # Calculate days until deadline
                days_until_deadline = (row['deadline'] - today).days
                
                # Check if today is one of the reminder days
                if days_until_deadline in row['days_before_deadline']:
                    # Get client info
                    client_result = self.db.client.table('clients').select('*').eq('id', row['client_id']).execute()
                    if not client_result.data:
                        continue
                    
                    client = client_result.data[0]
                    
                    # Get reminder type and template info
                    reminder_type_result = self.db.client.table('reminder_type_info').select('*').eq('reminder_type_id', row['reminder_type_id']).execute()
                    if not reminder_type_result.data:
                        continue
                    
                    reminder_type = reminder_type_result.data[0]
                    
                    template_result = self.db.client.table('email_template').select('*').eq('template_id', reminder_type['email_template_id']).execute()
                    if not template_result.data:
                        continue
                    
                    template = template_result.data[0]
                    
                    reminder_data = ReminderData(
                        reminder_id=row['reminder_id'],
                        client_id=row['client_id'],
                        group_id=row.get('group_id'),
                        reminder_type_id=row['reminder_type_id'],
                        deadline=row['deadline'],
                        days_before_deadline=row['days_before_deadline'],
                        client_email=client.get('email'),
                        client_name=client.get('first_name', '') + ' ' + client.get('last_name', '') or client.get('company_name', ''),
                        template_subject=template['subject'],
                        template_body=template['body'],
                        template_name=template['name'],
                        reminder_type_name=reminder_type['name']
                    )
                    reminders.append(reminder_data)
            
            return reminders
            
        except Exception as e:
            logger.error(f"Error fetching reminders: {str(e)}")
            return []
    
    def is_client_blocklisted(self, client_id: int) -> bool:
        """Check if client is in blocklist"""
        try:
            result = self.db.client.table('reminder_blocklist').select('*').eq('client_id', client_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error checking blocklist for client {client_id}: {str(e)}")
            return False
    
    def is_client_unsubscribed(self, client_id: int, reminder_id: int) -> bool:
        """Check if client has unsubscribed from this specific reminder"""
        try:
            result = self.db.client.table('reminder_unsubscribers').select('*').eq('client_id', client_id).eq('reminder_id', reminder_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error checking unsubscribe for client {client_id}, reminder {reminder_id}: {str(e)}")
            return False
    
    def update_reminder_status(self, reminder_id: int, client_id: int, status: str, error_message: str = None):
        """Update reminder status in database"""
        try:
            status_data = {
                'reminder_id': reminder_id,
                'client_id': client_id,
                'status': status,
                'error_message': error_message
            }
            
            self.db.client.table('reminder_status').insert(status_data).execute()
            logger.info(f"Updated status for reminder {reminder_id}, client {client_id}: {status}")
            
        except Exception as e:
            logger.error(f"Error updating reminder status: {str(e)}")
    
    def process_reminders(self):
        """Main method to process all reminders for today"""
        logger.info("Starting reminder processing...")
        
        reminders = self.get_todays_reminders()
        logger.info(f"Found {len(reminders)} reminders to process")
        
        success_count = 0
        error_count = 0
        
        for reminder in reminders:
            try:
                # Check if client has email
                if not reminder.client_email:
                    self.update_reminder_status(reminder.reminder_id, reminder.client_id, 'error', 'No email address')
                    error_count += 1
                    continue
                
                # Check blocklist
                if self.is_client_blocklisted(reminder.client_id):
                    self.update_reminder_status(reminder.reminder_id, reminder.client_id, 'blocked', 'Client in blocklist')
                    logger.info(f"Client {reminder.client_id} is blocklisted, skipping")
                    continue
                
                # Check unsubscribe
                if self.is_client_unsubscribed(reminder.client_id, reminder.reminder_id):
                    self.update_reminder_status(reminder.reminder_id, reminder.client_id, 'unsubscribed', 'Client unsubscribed')
                    logger.info(f"Client {reminder.client_id} unsubscribed from reminder {reminder.reminder_id}")
                    continue
                
                # Personalize email content
                personalized_subject = self._personalize_content(reminder.template_subject, reminder)
                personalized_body = self._personalize_content(reminder.template_body, reminder)
                
                # Send email
                result = self.mailer.send_email(
                    to_email=reminder.client_email,
                    to_name=reminder.client_name,
                    subject=personalized_subject,
                    body=personalized_body
                )
                
                if result['success']:
                    self.update_reminder_status(reminder.reminder_id, reminder.client_id, 'sent')
                    success_count += 1
                    logger.info(f"Successfully sent reminder {reminder.reminder_id} to {reminder.client_email}")
                else:
                    self.update_reminder_status(reminder.reminder_id, reminder.client_id, 'error', result.get('error', 'Unknown error'))
                    error_count += 1
                    logger.error(f"Failed to send reminder {reminder.reminder_id} to {reminder.client_email}")
                
            except Exception as e:
                self.update_reminder_status(reminder.reminder_id, reminder.client_id, 'error', str(e))
                error_count += 1
                logger.error(f"Error processing reminder {reminder.reminder_id}: {str(e)}")
        
        logger.info(f"Reminder processing completed. Success: {success_count}, Errors: {error_count}")
        return success_count, error_count
    
    def _personalize_content(self, content: str, reminder: ReminderData) -> str:
        """Personalize email content with client and reminder data"""
        # Replace placeholders with actual data
        personalized = content.replace('{{client_name}}', reminder.client_name)
        personalized = personalized.replace('{{deadline}}', str(reminder.deadline))
        personalized = personalized.replace('{{reminder_type}}', reminder.reminder_type_name)
        personalized = personalized.replace('{{days_until_deadline}}', str((reminder.deadline - date.today()).days))
        
        return personalized 