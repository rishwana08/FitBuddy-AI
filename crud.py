from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from .models import Plan, User
from .schemas import UserInput


def get_user(
    db: Session,
    user_id: str,
) -> User | None:

    return db.scalar(
        select(User)
        .where(User.user_id == user_id)
        .options(joinedload(User.plan))
    )


def get_all_users(
    db: Session,
) -> list[User]:

    return list(
        db.scalars(
            select(User)
            .options(joinedload(User.plan))
            .order_by(User.created_at.desc())
        ).unique()
    )


def save_user(
    db: Session,
    data: UserInput,
) -> User:

    user = get_user(
        db,
        data.user_id,
    )

    if user is None:

        user = User(
            user_id=data.user_id,
            name=data.name,
            age=data.age,
            weight=data.weight,
            goal=data.goal,
            intensity=data.intensity,
        )

        db.add(user)

    else:

        user.name = data.name
        user.age = data.age
        user.weight = data.weight
        user.goal = data.goal
        user.intensity = data.intensity

    db.flush()

    return user


def save_plan(
    db: Session,
    user: User,
    workout_plan: str,
    nutrition_tip: str,
) -> Plan:

    if user.plan is None:

        plan = Plan(
            user_id=user.id,
            original_plan=workout_plan,
            nutrition_tip=nutrition_tip,
        )

        db.add(plan)

    else:

        plan = user.plan

        plan.original_plan = workout_plan
        plan.updated_plan = None
        plan.feedback = None
        plan.nutrition_tip = nutrition_tip

    db.commit()

    db.refresh(plan)

    return plan


def update_plan(
    db: Session,
    plan: Plan,
    updated_plan: str,
    feedback: str,
    nutrition_tip: str,
) -> Plan:

    plan.updated_plan = updated_plan
    plan.feedback = feedback
    plan.nutrition_tip = nutrition_tip

    db.commit()

    db.refresh(plan)

    return plan


def delete_user(
    db: Session,
    user_id: str,
) -> bool:

    user = db.scalar(
        select(User).where(
            User.user_id == user_id
        )
    )

    if user is None:
        return False

    db.delete(user)

    db.commit()

    return True