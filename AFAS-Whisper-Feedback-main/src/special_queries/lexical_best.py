from sqlalchemy.orm import Session



def get_best_lexical_user(db: Session):
    return (
        db.query(
            db.models.Submit.user_id,
            db.models.Lexical.mttr,
            db.models.Lexical.B2,
            db.models.Lexical.C1
        )
        .join(
            db.models.Lexical,
            db.models.Lexical.submit_id == db.models.Submit.id
        )
        .order_by(
            (db.models.Lexical.B2 + db.models.Lexical.C1).desc(),
            db.models.Lexical.mttr.desc()
        )
        .first()
    )