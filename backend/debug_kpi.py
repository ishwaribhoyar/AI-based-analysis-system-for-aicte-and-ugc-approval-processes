from config.database import get_db, Block, Batch, close_db
from services.kpi import KPIService
db = get_db()

# Get the latest AICTE batch
batch = db.query(Batch).filter(Batch.mode == 'aicte').order_by(Batch.id.desc()).first()
print(f'Latest batch: {batch.id}')

blocks = db.query(Block).filter(Block.batch_id == batch.id).all()
print(f'Found {len(blocks)} blocks')

block_list = []
for block in blocks:
    block_dict = {
        'block_type': block.block_type,
        'extracted_data': block.data or {}
    }
    block_list.append(block_dict)
    data = block.data or {}
    print(f'{block.block_type}:')
    if 'total_students_num' in data:
        print(f'  total_students_num: {data["total_students_num"]}')
    if 'built_up_area_sqm_num' in data:
        print(f'  built_up_area_sqm_num: {data["built_up_area_sqm_num"]}')

# Now calculate KPIs
print('\n--- Calculating KPIs ---')
kpi = KPIService()
results = kpi.calculate_kpis('aicte', blocks=block_list)
print()
print('KPI Results:')
for key, val in results.items():
    if isinstance(val, dict):
        print(f'  {key}: {val.get("value")}')
    else:
        print(f'  {key}: {val}')
close_db(db)
