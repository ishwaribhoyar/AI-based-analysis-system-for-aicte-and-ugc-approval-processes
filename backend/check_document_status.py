"""Quick script to check document processing status"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['reviewer_db']
    
    # Get latest batch
    batches = await db.batches.find().sort('created_at', -1).limit(1).to_list(1)
    if not batches:
        print("No batches found")
        return
    
    batch = batches[0]
    batch_id = batch['batch_id']
    print(f"\n📦 Latest Batch: {batch_id}")
    print(f"   Mode: {batch.get('mode')}")
    print(f"   Status: {batch.get('status')}")
    print(f"   Total Documents: {batch.get('total_documents', 0)}")
    
    # Get documents
    docs = await db.documents.find({'batch_id': batch_id}).to_list(100)
    print(f"\n📄 Documents ({len(docs)}):")
    
    for doc in docs:
        filename = doc.get('filename', 'unknown')
        status = doc.get('status', 'unknown')
        doc_type = doc.get('doc_type', 'NOT CLASSIFIED')
        has_extracted_data = bool(doc.get('extracted_data'))
        has_text = bool(doc.get('extracted_text'))
        text_length = len(doc.get('extracted_text', ''))
        errors = doc.get('processing_errors', [])
        
        print(f"\n   📄 {filename}")
        print(f"      Status: {status}")
        print(f"      Doc Type: {doc_type}")
        print(f"      Has Text: {has_text} (length: {text_length})")
        print(f"      Has Extracted Data: {has_extracted_data}")
        if errors:
            print(f"      Errors: {errors}")
    
    # Check sufficiency
    sufficiency = batch.get('sufficiency_result')
    if sufficiency:
        print(f"\n✅ Sufficiency Result:")
        print(f"   Percentage: {sufficiency.get('percentage', 0)}%")
        print(f"   Present: {sufficiency.get('present_count', 0)}/{sufficiency.get('required_count', 0)}")
        print(f"   Missing: {sufficiency.get('missing_blocks', [])}")
    else:
        print(f"\n⚠️  No sufficiency result stored")
    
    # Check KPIs
    kpis = batch.get('kpi_results')
    if kpis:
        print(f"\n📊 KPI Results: {len(kpis)} metrics")
    else:
        print(f"\n⚠️  No KPI results stored")

if __name__ == "__main__":
    asyncio.run(check())

