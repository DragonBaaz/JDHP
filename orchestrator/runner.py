import json
import datetime
import uuid
import os
from db.models import db, Job, AgentRun
from agents.topic_selection import TopicSelectionAgent
from agents.market_analysis import MarketAnalysisAgent
from agents.data_collection import DataCollectionAgent
from agents.research import ResearchAgent
from agents.editing import EditingAgent
from agents.design import DesignAgent
from agents.publishing import PublishingAgent
from agents.marketing import MarketingAgent
from agents.feedback import FeedbackAgent

PIPELINE_STAGES = [
    {"name": "TopicSelectionAgent",  "depends_on": []},
    {"name": "MarketAnalysisAgent",  "depends_on": ["TopicSelectionAgent"]},
    {"name": "DataCollectionAgent",  "depends_on": ["MarketAnalysisAgent"]},
    {"name": "ResearchAgent",        "depends_on": ["DataCollectionAgent"]},
    {"name": "EditingAgent",         "depends_on": ["ResearchAgent"]},
    {"name": "DesignAgent",          "depends_on": ["EditingAgent"]},
    {"name": "PublishingAgent",      "depends_on": ["DesignAgent"]},
    {"name": "MarketingAgent",       "depends_on": ["PublishingAgent"]},
]

def _load(run: AgentRun) -> dict:
    """Safely deserialise stored agent output payload."""
    return json.loads(run.output_payload)

class Orchestrator:
    def __init__(self, config):
        self.config = config
        self.agents = {
            "TopicSelectionAgent": TopicSelectionAgent(config),
            "MarketAnalysisAgent": MarketAnalysisAgent(config),
            "DataCollectionAgent": DataCollectionAgent(config),
            "ResearchAgent":       ResearchAgent(config),
            "EditingAgent":        EditingAgent(config),
            "DesignAgent":         DesignAgent(config),
            "PublishingAgent":     PublishingAgent(config),
            "MarketingAgent":      MarketingAgent(config),
            "FeedbackAgent":       FeedbackAgent(config),
        }

    def _runs(self, job: Job) -> dict:
        return {r.agent_name: r for r in job.agent_runs}

    def _build_payload(self, stage_name: str, job: Job) -> dict:
        runs = self._runs(job)
        topic = job.approved_topic or job.topic

        if stage_name == "TopicSelectionAgent":
            return {"category_hint": job.topic, "exclude_topics": [], "max_topics": 5}

        elif stage_name == "MarketAnalysisAgent":
            return {"topic": topic, "target_audience": "Indian policy researchers and investors"}

        elif stage_name == "DataCollectionAgent":
            return {"topic": topic, "data_needs": []}

        elif stage_name == "ResearchAgent":
            market = _load(runs["MarketAnalysisAgent"])
            data = _load(runs["DataCollectionAgent"])
            return {
                "topic": topic,
                "target_audience": market.get("audience_size_estimate", "general audience"),
                "supplementary_data": data.get("datasets", []),
            }

        elif stage_name == "EditingAgent":
            research = _load(runs["ResearchAgent"])
            return {
                "report_markdown": research.get("report_markdown", ""),
                "target_audience": "Indian policy researchers and investors",
                "quality_flags": research.get("quality_flags", []),
            }

        elif stage_name == "DesignAgent":
            editing = _load(runs["EditingAgent"])
            topic_data = _load(runs["TopicSelectionAgent"]).get("topics", [{}])[0]
            return {
                "edited_markdown": editing.get("edited_markdown", ""),
                "report_title": topic,
                "target_audience": topic_data.get("target_audience", "general"),
                "price_inr": topic_data.get("estimated_price_inr", 1000),
            }

        elif stage_name == "PublishingAgent":
            design = _load(runs["DesignAgent"])
            topic_data = _load(runs["TopicSelectionAgent"]).get("topics", [{}])[0]
            editing = _load(runs["EditingAgent"])
            # Build description from first 400 chars of executive summary
            md = editing.get("edited_markdown", "")
            exec_summary = ""
            if "## Executive Summary" in md:
                exec_summary = md.split("## Executive Summary")[1].split("##")[0].strip()[:400]
            return {
                "pdf_path": design.get("pdf_path", ""),
                "report_title": topic,
                "description_markdown": exec_summary or f"In-depth research report on {topic}.",
                "price_inr": topic_data.get("estimated_price_inr", 1000),
                "tags": ["research", "india", topic.split()[0].lower()],
            }

        elif stage_name == "MarketingAgent":
            publishing = _load(runs["PublishingAgent"])
            editing = _load(runs["EditingAgent"])
            topic_data = _load(runs["TopicSelectionAgent"]).get("topics", [{}])[0]
            md = editing.get("edited_markdown", "")
            exec_summary = ""
            if "## Executive Summary" in md:
                exec_summary = md.split("## Executive Summary")[1].split("##")[0].strip()[:400]
            return {
                "report_title": topic,
                "gumroad_url": publishing.get("gumroad_url", ""),
                "description_markdown": exec_summary,
                "target_audience": topic_data.get("target_audience", "researchers"),
                "price_inr": topic_data.get("estimated_price_inr", 1000),
            }

        return {}

    def start(self, topic: str) -> str:
        """Create a new job and run the pipeline. Returns job_id."""
        db.connect(reuse_if_open=True)
        job = Job.create(
            id=str(uuid.uuid4()),
            topic=topic,
            approved_topic=None,
            status="running",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now()
        )
        print(f"\nJob created: {job.id}")
        self._run(job)
        return str(job.id)

    def resume(self, job_id: str, approved: bool, reason: str = "", approved_topic: str = ""):
        """Resume a paused job after gate approval or rejection."""
        db.connect(reuse_if_open=True)
        job = Job.get_by_id(job_id)

        if not approved:
            job.status = "abandoned"
            job.updated_at = datetime.datetime.now()
            job.save()
            print(f"Job {job_id} abandoned. Reason: {reason}")
            return

        # If operator approved a specific topic from Gate 1, store it
        if approved_topic:
            job.approved_topic = approved_topic

        # Determine which agent is paused
        paused_agent = None
        if job.status.startswith("paused_"):
            paused_agent = job.status.replace("paused_", "")
        
        # Special case: If paused at PublishingAgent (Gate 3), publish the product live
        if paused_agent == "PublishingAgent":
            runs = self._runs(job)
            if "PublishingAgent" in runs:
                pub_payload = _load(runs["PublishingAgent"])
                product_id = pub_payload.get("gumroad_product_id")
                if product_id:
                    print(f"Publishing Gumroad product {product_id}...")
                    try:
                        self.agents["PublishingAgent"].publish(product_id)
                    except Exception as e:
                        print(f"Warning: publish call failed: {e}")
        
        # Mark the paused agent as success so pipeline can progress
        if paused_agent:
            runs = self._runs(job)
            if paused_agent in runs:
                agent_run = runs[paused_agent]
                agent_run.status = "success"
                agent_run.save()
        
        job.status = "running"
        job.updated_at = datetime.datetime.now()
        job.save()

        self._run(job)

    def _run(self, job: Job):
        for stage in PIPELINE_STAGES:
            agent_name = stage["name"]

            # Skip already-succeeded stages
            runs = self._runs(job)
            existing = runs.get(agent_name)
            if existing and existing.status == "success":
                continue

            # Check dependencies
            deps_ok = all(
                runs.get(dep) and runs[dep].status == "success"
                for dep in stage["depends_on"]
            )
            if not deps_ok:
                print(f"Dependencies not met for {agent_name}. Stopping.")
                break

            payload = self._build_payload(agent_name, job)
            now = datetime.datetime.now()
            run_record = AgentRun.create(
                id=str(uuid.uuid4()),
                job=job,
                agent_name=agent_name,
                input_payload=json.dumps(payload),
                output_payload="{}",
                status="running",
                started_at=now,
                finished_at=now,
                error=None
            )

            print(f"  → {agent_name}...", end=" ", flush=True)
            output = self.agents[agent_name].run({"job_id": str(job.id), "payload": payload})

            run_record.output_payload = json.dumps(output.get("payload", {}))
            run_record.status = output["status"]
            run_record.error = output.get("error")
            run_record.finished_at = datetime.datetime.now()
            run_record.save()

            status = output["status"]
            print(status)

            if status == "needs_human":
                job.status = f"paused_{agent_name}"
                job.updated_at = datetime.datetime.now()
                job.save()
                print(f"\n⏸  GATE — human review required ({agent_name})")
                self._print_gate_info(agent_name, output["payload"])
                return

            elif status in ("failed", "needs_retry"):
                job.status = "failed"
                job.updated_at = datetime.datetime.now()
                job.save()
                print(f"\n✗ Pipeline failed at {agent_name}: {output.get('error')}")
                return

        job.status = "completed"
        job.updated_at = datetime.datetime.now()
        job.save()
        print("\n✓ Pipeline completed.")

    def _print_gate_info(self, agent_name: str, payload: dict):
        if agent_name == "TopicSelectionAgent":
            print("\nTopics generated (approve with --approve --topic-index N):")
            for i, t in enumerate(payload.get("topics", [])):
                print(f"  [{i}] {t.get('title')} | ₹{t.get('estimated_price_inr')} | {t.get('target_audience')}")
        elif agent_name == "ResearchAgent":
            wc = payload.get("word_count", "?")
            print(f"\nDraft ready: {wc} words. Review and approve with --approve.")
        elif agent_name == "PublishingAgent":
            print(f"\nGumroad draft created: {payload.get('gumroad_url')}")
            print("Review the listing, then approve with --approve to publish live.")
        print(f"\nResume: python run.py --resume <JOB_ID> --approve [--topic-index N]")

    def run_feedback(self, job_id: str):
        """Run FeedbackAgent for a completed job (call manually after 7 days)."""
        db.connect(reuse_if_open=True)
        job = Job.get_by_id(job_id)
        runs = self._runs(job)
        pub = runs.get("PublishingAgent")
        if not pub:
            print("PublishingAgent has not run for this job.")
            return
        pub_data = _load(pub)
        payload = {
            "gumroad_product_id": pub_data.get("gumroad_product_id", ""),
            "days_since_publish": 7
        }
        output = self.agents["FeedbackAgent"].run({"job_id": job_id, "payload": payload})
        if output["status"] == "success":
            p = output["payload"]
            job.revenue_inr = p.get("revenue_inr", 0)
            job.save()
            print(f"Sales: {p['sale_count']} | Revenue: ₹{p['revenue_inr']} | Avg rating: {p['avg_rating']}")
            if p.get("next_topic_hints"):
                print(f"Suggested next topics: {p['next_topic_hints']}")
        else:
            print(f"FeedbackAgent failed: {output.get('error')}")

    def dashboard(self):
        """Print a rich terminal table of all jobs."""
        try:
            from rich.console import Console
            from rich.table import Table
            console = Console()
            table = Table(title="JDHP Jobs")
            table.add_column("Job ID", style="cyan", width=10)
            table.add_column("Topic", style="white", width=45)
            table.add_column("Status", style="green", width=20)
            table.add_column("Revenue ₹", style="magenta", width=10)
            table.add_column("Created", style="yellow", width=16)
            db.connect(reuse_if_open=True)
            for job in Job.select().order_by(Job.created_at.desc()).limit(20):
                table.add_row(
                    str(job.id)[:8],
                    (job.approved_topic or job.topic)[:44],
                    job.status,
                    str(job.revenue_inr or "—"),
                    job.created_at.strftime("%Y-%m-%d %H:%M") if job.created_at else "—"
                )
            console.print(table)
        except ImportError:
            db.connect(reuse_if_open=True)
            print(f"{'ID':10} {'Topic':45} {'Status':20} {'Revenue':10}")
            for job in Job.select().order_by(Job.created_at.desc()).limit(20):
                print(f"{str(job.id)[:8]:10} {(job.approved_topic or job.topic)[:44]:45} {job.status:20} {str(job.revenue_inr or '—'):10}")
