import uuid

from config.database import get_db, close_db, Batch
from services.ranking_service import rank_institutions


def _seed_batches(batches):
    db = get_db()
    try:
        for entry in batches:
            batch = Batch(
                id=entry["id"],
                mode=entry.get("mode", "ugc"),
                status="completed",
                kpi_results=entry["kpis"],
            )
            db.merge(batch)  # upsert to avoid unique conflicts
        db.commit()
    finally:
        close_db(db)


def test_rank_overall_descending_order():
    b1 = f"batch_{uuid.uuid4().hex[:8]}"
    b2 = f"batch_{uuid.uuid4().hex[:8]}"
    b3 = f"batch_{uuid.uuid4().hex[:8]}"

    _seed_batches([
        {"id": b1, "kpis": {"overall_score": 82, "fsr_score": 70, "placement_index": 68}},
        {"id": b2, "kpis": {"overall_score": 91, "fsr_score": 74, "placement_index": 80}},
        {"id": b3, "kpis": {"overall_score": 77, "fsr_score": 66, "placement_index": 60}},
    ])

    result = rank_institutions([b1, b2, b3], {"overall_score": 1}, 3, "Overall Score")
    ranking_ids = [inst["batch_id"] for inst in result["institutions"]]

    assert ranking_ids == [b2, b1, b3]
    assert result["institutions"][0]["overall_score"] == 91


def test_rank_skips_missing_required_kpi():
    good_batch = f"batch_{uuid.uuid4().hex[:8]}"
    missing_batch = f"batch_{uuid.uuid4().hex[:8]}"

    _seed_batches([
        {"id": good_batch, "kpis": {"placement_index": 75, "overall_score": 80}},
        {"id": missing_batch, "kpis": {"fsr_score": 90}},  # placement missing
    ])

    result = rank_institutions([good_batch, missing_batch], {"placement_index": 1}, 2, "Placement Index")
    ranking_ids = [inst["batch_id"] for inst in result["institutions"]]

    assert ranking_ids == [good_batch]
    assert any(skip["batch_id"] == missing_batch for skip in result["insufficient_batches"])


def test_rank_with_weights_prefers_weighted_kpi():
    a = f"batch_{uuid.uuid4().hex[:8]}"
    b = f"batch_{uuid.uuid4().hex[:8]}"
    c = f"batch_{uuid.uuid4().hex[:8]}"

    _seed_batches([
        {"id": a, "kpis": {"fsr_score": 90, "placement_index": 50, "overall_score": 70}},
        {"id": b, "kpis": {"fsr_score": 70, "placement_index": 90, "overall_score": 75}},
        {"id": c, "kpis": {"fsr_score": 80, "placement_index": 80, "overall_score": 80}},
    ])

    weights = {"fsr_score": 1, "placement_index": 2, "overall_score": 0}
    result = rank_institutions([a, b, c], weights, 3, "Weighted KPI Mix")
    ranking_ids = [inst["batch_id"] for inst in result["institutions"]]

    # placement has double weight so batch b should lead
    assert ranking_ids[0] == b
    assert ranking_ids[1] == c
    assert ranking_ids[2] == a


def test_rank_handles_top_n_greater_than_available():
    b1 = f"batch_{uuid.uuid4().hex[:8]}"
    b2 = f"batch_{uuid.uuid4().hex[:8]}"

    _seed_batches([
        {"id": b1, "kpis": {"overall_score": 88, "fsr_score": 77}},
        {"id": b2, "kpis": {"overall_score": 79, "fsr_score": 70}},
    ])

    result = rank_institutions([b1, b2], {"overall_score": 1}, 5, "Overall Score")
    assert len(result["institutions"]) == 2
    assert {inst["batch_id"] for inst in result["institutions"]} == {b1, b2}

