#!/usr/bin/env python3
"""
Command-line interface for the Quicket Event Scraper.
"""

import argparse
import logging
import os
import shutil
import sys
from quicket_scraper import QuicketScraper

def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('scraper.log')
        ]
    )


def create_or_clear_directory(directory_path: str, logger: logging.Logger):
    """Create output directory if it doesn't exist."""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        logger.info(f"Created output directory: {directory_path}")
    else:
        # Clear existing files in the output directory
        for file in os.listdir(directory_path):
            file_path = os.path.join(directory_path, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logger.warning(f"Error clearing file {file_path}: {e}")
        logger.info(f"Cleared existing files in output directory: {directory_path}")

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Scrape events from Quicket website.')
    parser.add_argument(
        '--pages', 
        type=int, 
        default=10,
        help='Maximum number of pages to scrape (default: 10)'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default='quicket_events.csv',
        help='Output CSV file name (default: quicket_events.csv)'
    )
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--headless', 
        action='store_true',
        help='Run browser in headless mode (default: True)'
    )
    
    return parser.parse_args()



def main():
    """Main function to run the scraper from command line."""
    args = parse_args()
    setup_logging(args.verbose)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting Quicket scraper with the following settings:")
    logger.info(f"Max pages: {args.pages}")
    logger.info(f"Output file: {args.output}")
    logger.info(f"Headless mode: {args.headless}")
    
    create_or_clear_directory("error_screenshots", logger)
    try:
        # Create and run the scraper
        scraper = QuicketScraper(max_pages=args.pages, headless=args.headless)
        events = scraper.scrape_events()
        
        # Save the results
        scraper.save_to_csv(args.output)
        logger.info(f"Scraping completed successfully. {len(events)} events saved to {args.output}")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Error during scraping: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 