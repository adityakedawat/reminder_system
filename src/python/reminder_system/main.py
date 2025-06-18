import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the reminder service
try:
    from reminder_service import ReminderService
except ImportError:
    # Fallback for when running as a module
    from .reminder_service import ReminderService


def main():
    """Main entry point for the reminder system"""
    try:
        logger.info("Starting reminder system...")
        
        # Initialize the reminder service
        reminder_service = ReminderService()
        
        # Process all reminders for today
        success_count, error_count = reminder_service.process_reminders()
        
        logger.info(f"Reminder processing completed successfully!")
        logger.info(f"Summary: {success_count} emails sent, {error_count} errors")
        
        # Exit with appropriate code for GitHub Actions
        if error_count == 0:
            logger.info("All reminders processed successfully")
            sys.exit(0)
        else:
            logger.warning(f"Completed with {error_count} errors")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error in reminder system: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
