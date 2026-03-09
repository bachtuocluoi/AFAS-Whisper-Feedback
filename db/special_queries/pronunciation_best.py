from sqlalchemy.orm import Session



def get_best_pronunciation_user(db: Session):
    return (
        db.query(
            db.models.Submit.user_id,
            db.models.Pronunciation.score_95_100,
            db.models.Pronunciation.score_85_95
        )
        .join(db.models.Pronunciation, db.models.Pronunciation.submit_id == db.models.Submit.id)
        .order_by(
            db.models.Pronunciation.score_95_100.desc(),
            db.models.Pronunciation.score_85_95.desc()
        )
        .first()
    )
