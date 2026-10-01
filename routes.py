from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Request,
)
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .crud import (
    delete_user,
    get_all_users,
    get_user,
    save_plan,
    save_user,
    update_plan,
)

from .database import get_db

from .gemini_service import (
    generate_nutrition_tip_with_flash,
    generate_workout_gemini,
    update_workout_plan,
)

from .schemas import (
    FeedbackRequest,
    GenerateResponse,
    UserInput,
    UserResponse,
)


router = APIRouter()


templates = Jinja2Templates(
    directory="templates"
)


def make_user_response(user) -> UserResponse:

    return UserResponse(
        user_id=user.user_id,
        name=user.name,
        age=user.age,
        weight=user.weight,
        goal=user.goal,
        intensity=user.intensity,
    )


# ==================================================
# HOME
# ==================================================

@router.get(
    "/",
    response_class=HTMLResponse,
)
def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "FitBuddy",
            "error": None,
        },
    )


# ==================================================
# GENERATE WORKOUT
# ==================================================

@router.post(
    "/generate-workout",
    response_class=HTMLResponse,
)
def generate_workout(

    request: Request,

    user_id: str = Form(...),

    name: str = Form(...),

    age: int = Form(...),

    weight: float = Form(...),

    goal: str = Form(...),

    intensity: str = Form(...),

    db: Session = Depends(get_db),
):

    try:

        user_data = UserInput(
            user_id=user_id,
            name=name,
            age=age,
            weight=weight,
            goal=goal,
            intensity=intensity,
        )

        workout_plan, workout_mode = (
            generate_workout_gemini(
                user_data
            )
        )

        nutrition_tip, tip_mode = (
            generate_nutrition_tip_with_flash(
                user_data.goal
            )
        )

        user = save_user(
            db,
            user_data,
        )

        plan = save_plan(
            db,
            user,
            workout_plan,
            nutrition_tip,
        )

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "title": "Your FitBuddy Plan",
                "user": user,
                "plan": plan,
                "ai_mode": (
                    f"{workout_mode} / {tip_mode}"
                ),
                "error": None,
                "message": None,
            },
        )

    except Exception as exc:

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "title": "FitBuddy",
                "error": str(exc),
            },
            status_code=400,
        )


# ==================================================
# FEEDBACK
# ==================================================

@router.post(
    "/submit-feedback",
    response_class=HTMLResponse,
)
def submit_feedback(

    request: Request,

    user_id: str = Form(...),

    feedback: str = Form(...),

    db: Session = Depends(get_db),
):

    try:

        request_data = FeedbackRequest(
            user_id=user_id,
            feedback=feedback,
        )

        user = get_user(
            db,
            request_data.user_id,
        )

        if user is None or user.plan is None:

            raise ValueError(
                "User or workout plan was not found."
            )

        user_data = UserInput(
            user_id=user.user_id,
            name=user.name,
            age=user.age,
            weight=user.weight,
            goal=user.goal,
            intensity=user.intensity,
        )

        updated_plan, workout_mode = (
            update_workout_plan(
                user_data,
                user.plan.original_plan,
                request_data.feedback,
            )
        )

        nutrition_tip, tip_mode = (
            generate_nutrition_tip_with_flash(
                user.goal
            )
        )

        plan = update_plan(
            db,
            user.plan,
            updated_plan,
            request_data.feedback,
            nutrition_tip,
        )

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "title": "Updated FitBuddy Plan",
                "user": user,
                "plan": plan,
                "ai_mode": (
                    f"{workout_mode} / {tip_mode}"
                ),
                "message": (
                    "Your workout plan was updated "
                    "using your feedback."
                ),
                "error": None,
            },
        )

    except Exception as exc:

        user = get_user(
            db,
            user_id,
        )

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "title": "FitBuddy",
                "user": user,
                "plan": (
                    user.plan
                    if user
                    else None
                ),
                "ai_mode": None,
                "message": None,
                "error": str(exc),
            },
            status_code=400,
        )


# ==================================================
# ADMIN
# ==================================================

@router.get(
    "/view-all-users",
    response_class=HTMLResponse,
)
def view_all_users(

    request: Request,

    db: Session = Depends(get_db),
):

    users = get_all_users(db)

    return templates.TemplateResponse(
        request=request,
        name="all_users.html",
        context={
            "title": "All Users",
            "users": users,
        },
    )


@router.post(
    "/admin/delete-user/{user_id}"
)
def admin_delete_user(

    user_id: str,

    db: Session = Depends(get_db),
):

    deleted = delete_user(
        db,
        user_id,
    )

    if not deleted:

        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return JSONResponse(
        {
            "message": (
                f"User {user_id} deleted."
            ),
            "user_id": user_id,
        }
    )


# ==================================================
# JSON API
# ==================================================

@router.get("/api/users")
def api_users(
    db: Session = Depends(get_db),
):

    users = get_all_users(db)

    return [
        make_user_response(user).model_dump()
        for user in users
    ]


@router.get(
    "/api/users/{user_id}"
)
def api_user(

    user_id: str,

    db: Session = Depends(get_db),
):

    user = get_user(
        db,
        user_id,
    )

    if user is None:

        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    plan_data = None

    if user.plan:

        plan_data = {
            "original_plan":
                user.plan.original_plan,

            "updated_plan":
                user.plan.updated_plan,

            "feedback":
                user.plan.feedback,

            "nutrition_tip":
                user.plan.nutrition_tip,
        }

    return {
        "user":
            make_user_response(
                user
            ).model_dump(),

        "plan":
            plan_data,
    }


@router.post(
    "/api/generate",
    response_model=GenerateResponse,
)
def api_generate(

    data: UserInput,

    db: Session = Depends(get_db),
):

    try:

        workout, workout_mode = (
            generate_workout_gemini(data)
        )

        tip, tip_mode = (
            generate_nutrition_tip_with_flash(
                data.goal
            )
        )

        user = save_user(
            db,
            data,
        )

        save_plan(
            db,
            user,
            workout,
            tip,
        )

        return GenerateResponse(
            user=make_user_response(
                user
            ),
            workout_plan=workout,
            nutrition_tip=tip,
            ai_mode=(
                f"{workout_mode} / {tip_mode}"
            ),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.post(
    "/api/feedback"
)
def api_feedback(

    data: FeedbackRequest,

    db: Session = Depends(get_db),
):

    user = get_user(
        db,
        data.user_id,
    )

    if user is None or user.plan is None:

        raise HTTPException(
            status_code=404,
            detail="User or plan not found",
        )

    user_data = UserInput(
        user_id=user.user_id,
        name=user.name,
        age=user.age,
        weight=user.weight,
        goal=user.goal,
        intensity=user.intensity,
    )

    try:

        updated_plan, workout_mode = (
            update_workout_plan(
                user_data,
                user.plan.original_plan,
                data.feedback,
            )
        )

        nutrition_tip, tip_mode = (
            generate_nutrition_tip_with_flash(
                user.goal
            )
        )

        plan = update_plan(
            db,
            user.plan,
            updated_plan,
            data.feedback,
            nutrition_tip,
        )

        return {
            "user_id":
                user.user_id,

            "updated_plan":
                plan.updated_plan,

            "nutrition_tip":
                plan.nutrition_tip,

            "ai_mode":
                f"{workout_mode} / {tip_mode}",
        }

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc