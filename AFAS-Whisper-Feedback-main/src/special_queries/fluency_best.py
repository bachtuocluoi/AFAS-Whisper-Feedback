from sqlalchemy.orm import Session


def get_most_fluent_user(db: Session):
    return (
        db.query(
            db.models.Submit.user_id,
            db.models.Fluency.speed_rate,
            db.models.Fluency.pause_ratio
        )
        .join(
            db.models.Fluency,
            db.models.Fluency.submit_id == db.models.Submit.id
        )
        .order_by(
            db.models.Fluency.pause_ratio.asc(),
            db.models.Fluency.speed_rate.desc()
        )
        .first()
    )