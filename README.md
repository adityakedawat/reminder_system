# Reminder System

A comprehensive reminder system that sends automated emails using RESEND API and Supabase as the database backend.

## Features

- **Automated Reminder Processing**: Daily cron job to send reminders based on deadlines
- **Email Integration**: Uses MailerSend API for reliable email delivery
- **Database Management**: Supabase integration for data storage and retrieval
- **Blocklist Support**: Prevents sending emails to blocked clients
- **Unsubscribe Management**: Respects client unsubscribe preferences
- **Status Tracking**: Tracks the status of each reminder sent
- **Personalization**: Supports template variables for personalized emails
- **Failure Notifications**: Email alerts when the reminder processing fails

## Database Schema

The system uses the following key tables:

- `clients`: Client information (name, email, company details)
- `reminder_info`: Reminder configurations with deadlines and notification schedules
- `reminder_type_info`: Types of reminders (e.g., tax filing, compliance)
- `email_template`: Email templates with subject and body content
- `reminder_status`: Tracking of sent reminders and their status
- `reminder_blocklist`: Clients who should not receive any reminders
- `reminder_unsubscribers`: Clients who unsubscribed from specific reminders

## Setup

### 1. Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_SECRET_KEY=your_supabase_secret_key

# MailerSend Configuration
RESEND_API_KEY=your_RESEND_API_KEY
RESEND_FROM_EMAIL=your_verified_sender_email
RESEND_FROM_NAME=Your Company Name
```

### 2. GitHub Secrets

For GitHub Actions, add the following secrets to your repository:

**Required:**
- `SUPABASE_URL`
- `SUPABASE_SECRET_KEY`
- `RESEND_API_KEY`
- `RESEND_FROM_EMAIL`
- `RESEND_FROM_NAME`

**For failure notifications:**
- `EMAIL_USERNAME` - Gmail address for sending notifications
- `EMAIL_PASSWORD` - Gmail app password (not regular password)
- `NOTIFICATION_EMAIL` - Email address to receive failure notifications

### 3. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install the reminder system package
pip install -e .
```

## Usage

### Running Locally

After installation, you can run the reminder system using the console script:

```bash
# Run the reminder processing script
reminder-system
```

Alternatively, you can run it as a module:

```bash
# Navigate to the reminder system directory and run
cd src/python/reminder_system
python main.py
```

Or import and use it in your own code:

```python
from reminder_system.reminder_service import ReminderService

# Initialize and run
service = ReminderService()
success_count, error_count = service.process_reminders()
```

### Testing Setup

```bash
# Run the test script to verify your configuration
python test_setup.py
```

### GitHub Actions

The system includes a GitHub Actions workflow that runs daily at 9:00 AM UTC. The workflow:

1. Checks out the code
2. Sets up Python environment
3. Installs dependencies
4. Installs the reminder system package
5. Runs the reminder processing
6. Sends email notifications on failure (if configured)

### Manual Trigger

You can manually trigger the workflow from the GitHub Actions tab in your repository.

## Email Templates

Email templates support the following variables:

- `{{client_name}}`: Client's full name or company name
- `{{deadline}}`: The deadline date
- `{{reminder_type}}`: Type of reminder
- `{{days_until_deadline}}`: Days remaining until deadline

Example template:
```html
<h2>Hello {{client_name}},</h2>
<p>This is a reminder that your {{reminder_type}} is due on {{deadline}}.</p>
<p>You have {{days_until_deadline}} days remaining.</p>
```

## Database Setup

Ensure your Supabase database has the required tables as defined in the schema. The system will automatically:

1. Query for reminders due today
2. Check blocklist and unsubscribe status
3. Personalize email content
4. Send emails via MailerSend
5. Update reminder status

## Monitoring

The system provides comprehensive logging:

- Success/failure counts for each run
- Detailed error messages for debugging
- Status tracking in the database
- Email notifications for failures

## Error Handling

The system handles various error scenarios:

- Missing email addresses
- Blocklisted clients
- Unsubscribed clients
- API failures
- Database connection issues

## Development

### Project Structure

```
src/python/reminder_system/
├── __init__.py
├── db.py              # Database connection
├── main.py            # Entry point
└── reminder_service.py # Core reminder logic
```

### Adding New Features

1. **New Reminder Types**: Add entries to `reminder_type_info` table
2. **New Email Templates**: Add templates to `email_template` table
3. **Custom Variables**: Extend the `_personalize_content` method

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**: Ensure all required environment variables are set
2. **Database Connection**: Verify Supabase credentials and network access
3. **MailerSend API**: Check API key and sender email verification
4. **Template Variables**: Ensure all variables in templates are supported
5. **Gmail App Password**: For failure notifications, use Gmail app password, not regular password

### Logs

Check the console output for detailed logs. The system logs:
- Number of reminders found
- Success/failure for each email
- Error details for debugging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License. 
