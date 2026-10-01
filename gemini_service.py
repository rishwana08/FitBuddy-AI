import logging

from .config import settings
from .schemas import UserInput


logger = logging.getLogger(__name__)


try:
    from google import genai
    from google.genai import types

except ImportError:
    genai = None
    types = None


def get_client():

    if not settings.gemini_api_key:
        return None

    if genai is None:
        return None

    return genai.Client(
        api_key=settings.gemini_api_key
    )


def generate_with_gemini(
    prompt: str,
    model: str,
) -> str | None:

    client = get_client()

    if client is None:
        return None

    try:

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.5,
                max_output_tokens=4000,
            ),
        )

        result = (response.text or "").strip()

        if result:
            return result

        return None

    except Exception:

        logger.exception(
            "Gemini API request failed"
        )

        return None


# --------------------------------------------------
# DEMO WORKOUT
# --------------------------------------------------

def demo_workout(
    user: UserInput,
) -> str:

    focus_map = {

        "weight loss":
            "full-body conditioning and cardio",

        "muscle gain":
            "strength training and progressive overload",

        "general wellness":
            "balanced full-body fitness",

        "flexibility":
            "mobility, flexibility and controlled strength",
    }

    focus = focus_map[user.goal]

    return f"""
FITBUDDY 7-DAY WORKOUT PLAN

Name: {user.name}
Goal: {user.goal.title()}
Intensity: {user.intensity.title()}

Primary Focus:
{focus}


DAY 1 – FULL BODY

Warm-up:
5–10 minutes brisk walking and dynamic mobility.

Main Workout:
• Squats – 3 × 10
• Push-ups – 3 × 8–12
• Glute bridges – 3 × 12
• Plank – 3 × 30 seconds

Cooldown:
5 minutes easy walking and stretching.


DAY 2 – CARDIO & CORE

Warm-up:
5–10 minutes easy cardio.

Main Workout:
• Brisk walking/cycling – 20–30 minutes
• Dead bugs – 3 × 10
• Side plank – 3 × 20 seconds per side

Cooldown:
5–10 minutes gentle stretching.


DAY 3 – UPPER BODY

Warm-up:
5–10 minutes shoulder and upper-body mobility.

Main Workout:
• Incline push-ups – 3 × 10
• Resistance-band rows – 3 × 12
• Shoulder press – 3 × 10
• Bird-dog – 3 × 10 per side

Cooldown:
Chest, shoulder and back stretching.


DAY 4 – RECOVERY

• 20–30 minutes easy walking
• 10–15 minutes mobility or gentle yoga
• Keep the effort comfortable


DAY 5 – LOWER BODY

Warm-up:
5–10 minutes easy cardio and leg mobility.

Main Workout:
• Squats – 3 × 10
• Reverse lunges – 3 × 8 per side
• Hip hinges – 3 × 10
• Calf raises – 3 × 15

Cooldown:
Lower-body stretching.


DAY 6 – CARDIO & CORE

Warm-up:
5–10 minutes easy cardio.

Main Workout:
• Moderate cardio – 20–30 minutes
• Mountain climbers – 3 × 20 seconds
• Plank – 3 × 30 seconds

Cooldown:
Slow walking and stretching.


DAY 7 – ACTIVE RECOVERY

• Easy walking – 20–30 minutes
• Full-body mobility
• Hydration
• Good sleep
• Gentle stretching


GENERAL SAFETY:

Rest 45–90 seconds between sets unless more recovery
is needed.

Stop exercise if you experience sharp pain, dizziness,
or unusual shortness of breath.

This is general fitness education and not medical advice.
"""


# --------------------------------------------------
# DEMO NUTRITION
# --------------------------------------------------

def demo_tip(
    goal: str,
) -> str:

    tips = {

        "weight loss":
            "Prioritize protein-rich foods, vegetables, whole grains and hydration. Focus on sustainable eating habits rather than extreme restriction.",

        "muscle gain":
            "Include a protein source in each meal and combine protein with carbohydrates after workouts to support recovery.",

        "general wellness":
            "Build meals around vegetables or fruit, a protein source, whole grains and healthy fats while staying well hydrated.",

        "flexibility":
            "Stay hydrated and include protein-rich foods along with fruits and vegetables to support general recovery.",
    }

    return tips.get(
        goal,
        tips["general wellness"],
    )


# --------------------------------------------------
# WORKOUT GENERATION
# --------------------------------------------------

def generate_workout_gemini(
    user: UserInput,
) -> tuple[str, str]:

    prompt = f"""
You are FitBuddy, a responsible fitness-planning assistant.

Create a practical 7-day workout plan.

USER INFORMATION:

Name: {user.name}
Age: {user.age}
Weight: {user.weight} kg
Fitness Goal: {user.goal}
Workout Intensity: {user.intensity}

REQUIREMENTS:

1. Create Day 1 through Day 7.
2. Include warm-up.
3. Include main workout.
4. Give exercise names.
5. Give sets/repetitions or duration.
6. Include cooldown or recovery.
7. Include suitable rest days.
8. Match the selected goal.
9. Match the selected intensity.
10. Keep the language simple.
11. Do not diagnose diseases.
12. Do not prescribe medical treatment.
13. Do not promise guaranteed results.
14. Mention basic exercise safety.
15. Return plain text.
16. Do not return JSON.

Make the plan practical for a general user.
"""

    result = generate_with_gemini(
        prompt,
        settings.workout_model,
    )

    if result:

        return result, "Gemini"

    if settings.demo_mode:

        return demo_workout(user), "Demo fallback"

    raise RuntimeError(
        "Gemini API is not configured or did not return a response."
    )


# --------------------------------------------------
# NUTRITION
# --------------------------------------------------

def generate_nutrition_tip_with_flash(
    goal: str,
) -> tuple[str, str]:

    prompt = f"""
Give one concise nutrition or recovery tip for:

Fitness goal: {goal}

Requirements:

• Practical
• General
• Safe
• 2–4 sentences
• No medical treatment
• No extreme diet recommendations

Return only the tip.
"""

    result = generate_with_gemini(
        prompt,
        settings.tip_model,
    )

    if result:

        return result, "Gemini"

    if settings.demo_mode:

        return demo_tip(goal), "Demo fallback"

    raise RuntimeError(
        "Gemini API is not configured or did not return a response."
    )


# --------------------------------------------------
# FEEDBACK UPDATE
# --------------------------------------------------

def update_workout_plan(
    user: UserInput,
    original_plan: str,
    feedback: str,
) -> tuple[str, str]:

    prompt = f"""
You are FitBuddy.

You must revise an existing 7-day fitness plan.

USER:

Name: {user.name}
Age: {user.age}
Weight: {user.weight} kg
Goal: {user.goal}
Intensity: {user.intensity}


ORIGINAL PLAN:

{original_plan}


USER FEEDBACK:

{feedback}


TASK:

Create a revised 7-day workout plan.

The revised plan should:

• Address the user's feedback.
• Keep the user's original fitness goal.
• Respect the selected intensity.
• Include Day 1 to Day 7.
• Include warm-ups.
• Include main workouts.
• Include sets/repetitions or duration.
• Include cooldown/recovery.
• Include suitable rest.
• Avoid medical diagnosis.
• Avoid medical treatment.
• Include a short safety reminder.

Return plain text only.
"""

    result = generate_with_gemini(
        prompt,
        settings.workout_model,
    )

    if result:

        return result, "Gemini"

    if settings.demo_mode:

        revised = (
            demo_workout(user)
            + "\n\n"
            + "FEEDBACK APPLIED\n\n"
            + f"Requested change: {feedback.strip()}"
        )

        return revised, "Demo fallback"

    raise RuntimeError(
        "Gemini API is not configured or did not return a response."
    )