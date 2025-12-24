from config.database import get_db, Block, Batch, close_db
import json

db = get_db()
batch = db.query(Batch).filter(Batch.mode == 'aicte').order_by(Batch.id.desc()).first()
print(f'Batch: {batch.id}')

blocks = db.query(Block).filter(Block.batch_id == batch.id, Block.block_type == 'student_enrollment_information').all()

for block in blocks:
    print('Student block data:')
    print(json.dumps(block.data, indent=2))
close_db(db)
