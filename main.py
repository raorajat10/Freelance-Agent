
"""
Lead Qualification Agent System
Main entry point
"""

import argparse
import sys
from pathlib import Path
from typing import List

from src.data.loader import DataLoader
from src.data.writer import DataWriter
from src.agents.website_inspector import WebsiteInspector
from src.agents.website_classifier import WebsiteClassifier
from src.agents.lead_scorer import LeadScorer
from src.agents.outreach_generator import OutreachGenerator
from src.models.schemas import LeadInput, LeadOutput


class LeadQualificationPipeline:
    """Main orchestrator for the 4-agent pipeline"""
    
    def __init__(self):
        self.inspector = WebsiteInspector()
        self.classifier = WebsiteClassifier()
        self.scorer = LeadScorer()
        self.outreach_gen = OutreachGenerator()
    
    def process_lead(self, lead: LeadInput) -> LeadOutput:
        """
        Process a single lead through all 4 agents
        
        Pipeline:
        1. Website Inspector → factual inspection
        2. Website Classifier → rule-based classification
        3. Lead Scorer → pure logic scoring
        4. Outreach Generator → LLM-based personalization
        """
        # Agent 1: Inspect website
        inspection = self.inspector.inspect(lead.website_url)
        
        # Agent 2: Classify website
        classification = self.classifier.classify(inspection)
        
        # Agent 3: Score lead
        scoring = self.scorer.score(lead, classification)
        
        # Agent 4: Generate outreach (only for high/medium priority)
        if scoring.priority.value in ['HIGH', 'MEDIUM']:
            outreach = self.outreach_gen.generate(lead, classification)
        else:
            outreach = "Low priority - no outreach generated"
        
        # Assemble final output
        return LeadOutput(
            business_name=lead.business_name,
            website_status=classification.website_status.value,
            website_issues=classification.issues,
            lead_score=scoring.lead_score,
            priority=scoring.priority.value,
            outreach_message=outreach
        )
    
    def process_batch(self, leads: List[LeadInput]) -> List[LeadOutput]:
        """Process multiple leads"""
        results = []
        total = len(leads)
        
        print(f"\n🚀 Processing {total} leads through 4-agent pipeline...\n")
        
        for idx, lead in enumerate(leads, 1):
            try:
                print(f"[{idx}/{total}] Processing: {lead.business_name}")
                result = self.process_lead(lead)
                results.append(result)
                print(f"  ✓ {result.priority} priority (score: {result.lead_score})")
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                # Create error output
                results.append(LeadOutput(
                    business_name=lead.business_name,
                    website_status="Error",
                    website_issues=[str(e)],
                    lead_score=0,
                    priority="LOW",
                    outreach_message="Processing failed"
                ))
        
        print(f"\n✓ Processed {len(results)} leads")
        return results
    
    def cleanup(self):
        """Clean up resources"""
        self.inspector.close()


def main():
    parser = argparse.ArgumentParser(
        description="Lead Qualification Agent System - Automatically qualify local business leads"
    )
    
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Input CSV file path'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='output/results.json',
        help='Output file path (supports .json or .csv)'
    )
    
    parser.add_argument(
        '--format',
        type=str,
        choices=['json', 'csv'],
        default='json',
        help='Output format'
    )
    
    args = parser.parse_args()
    
    # Validate input file exists
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Error: Input file not found: {args.input}")
        sys.exit(1)
    
    # Create output directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load data
        print(f"📥 Loading leads from {args.input}")
        leads = DataLoader.load_from_csv(args.input)
        
        if not leads:
            print("❌ No valid leads found")
            sys.exit(1)
        
        # Process leads
        pipeline = LeadQualificationPipeline()
        results = pipeline.process_batch(leads)
        
        # Write results
        print(f"\n💾 Writing results to {args.output}")
        if args.format == 'json':
            DataWriter.write_to_json(results, args.output)
        else:
            DataWriter.write_to_csv(results, args.output)
        
        # Summary statistics
        high_priority = sum(1 for r in results if r.priority == 'HIGH')
        medium_priority = sum(1 for r in results if r.priority == 'MEDIUM')
        low_priority = sum(1 for r in results if r.priority == 'LOW')
        
        print(f"\n📊 Summary:")
        print(f"  HIGH priority:   {high_priority}")
        print(f"  MEDIUM priority: {medium_priority}")
        print(f"  LOW priority:    {low_priority}")
        print(f"\n✅ Processing complete!")
        
        # Cleanup
        pipeline.cleanup()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


