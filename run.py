#!/usr/bin/env python3
"""
JDHP CLI — Agentic Publishing House entry point.

Usage:
  python run.py --topic "SEBI Small and Medium REITs India 2025"
  python run.py --resume <JOB_ID> --approve [--topic-index 0]
  python run.py --resume <JOB_ID> --reject --reason "too broad"
  python run.py --feedback --job-id <JOB_ID>
  python run.py --dashboard
"""
import argparse
import logging
import sys
import os

# Make sure project root is on path when run from any directory
sys.path.insert(0, os.path.dirname(__file__))

from config import config
from db.models import db, Job, AgentRun, init_db
from orchestrator.runner import Orchestrator

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join("logs", "jdhp.log"), encoding="utf-8")
    ]
)

def ensure_db():
    os.makedirs("logs", exist_ok=True)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    if not os.path.exists(config.DB_PATH):
        init_db()
    else:
        db.connect(reuse_if_open=True)

def main():
    parser = argparse.ArgumentParser(description="JDHP Agentic Publishing House")
    parser.add_argument("--topic", help="Topic category to start a new pipeline")
    parser.add_argument("--resume", metavar="JOB_ID", help="Resume a paused job")
    parser.add_argument("--approve", action="store_true", help="Approve at current gate")
    parser.add_argument("--reject", action="store_true", help="Reject and abandon job")
    parser.add_argument("--reason", default="", help="Reason for rejection")
    parser.add_argument("--topic-index", type=int, default=0,
                        help="Index of approved topic from Gate 1 topic list (default: 0)")
    parser.add_argument("--feedback", action="store_true", help="Run FeedbackAgent")
    parser.add_argument("--job-id", help="Job ID for --feedback")
    parser.add_argument("--dashboard", action="store_true", help="Show job status table")
    parser.add_argument("--init-db", action="store_true", help="Initialise the SQLite database")
    args = parser.parse_args()

    if args.init_db:
        init_db()
        return

    ensure_db()
    orch = Orchestrator(config)

    if args.topic:
        job_id = orch.start(args.topic)
        print(f"\nJob ID: {job_id}  (save this to resume after gates)")

    elif args.resume:
        if not args.approve and not args.reject:
            parser.error("--resume requires --approve or --reject")

        approved_topic = ""
        if args.approve:
            # Look up the topic title from the stored TopicSelectionAgent output
            try:
                db.connect(reuse_if_open=True)
                job = Job.get_by_id(args.resume)
                run = next((r for r in job.agent_runs if r.agent_name == "TopicSelectionAgent"), None)
                if run and run.output_payload:
                    import json
                    topics = json.loads(run.output_payload).get("topics", [])
                    if topics:
                        idx = min(args.topic_index, len(topics) - 1)
                        approved_topic = topics[idx].get("title", "")
                        print(f"Approved topic [{idx}]: {approved_topic}")
            except Exception as e:
                print(f"Warning: could not read topic list ({e})")

        orch.resume(
            job_id=args.resume,
            approved=args.approve,
            reason=args.reason,
            approved_topic=approved_topic
        )

    elif args.feedback:
        if not args.job_id:
            parser.error("--feedback requires --job-id")
        orch.run_feedback(args.job_id)

    elif args.dashboard:
        orch.dashboard()

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
