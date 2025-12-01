"""
Power handlers - Contains the logic for each shop power.
This keeps the power effects in code rather than database.
"""

from django.db import transaction
import logging

logger = logging.getLogger(__name__)


class PowerHandler:
    """Base class for power handlers"""

    power_type = None  # Must be overridden
    name = "Unknown Power"
    description = "No description"
    icon = """<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
    </svg>"""
    cost = 0

    @classmethod
    def can_use(cls, team, task=None, tasksolution=None):
        """
        Check if the power can be used in this context.
        Returns (can_use: bool, reason: str)
        """
        raise NotImplementedError

    @classmethod
    def use(cls, team, task=None, tasksolution=None):
        """
        Execute the power effect.
        Returns (success: bool, message: str)
        """
        raise NotImplementedError

    @classmethod
    def get_power_info(cls):
        """Return power metadata for shop display"""
        return {
            "power_type": cls.power_type,
            "name": cls.name,
            "description": cls.description,
            "icon": cls.icon,
            "cost": cls.cost,
        }


class TimeMachinePower(PowerHandler):
    """Gives one extra attempt on a max-attempts task"""

    power_type = "time_machine"
    name = "Time Machine"
    description = "Turn back time and get one extra attempt on any challenge that has reached maximum attempts. Use wisely!"
    icon = """<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <polyline points="12 6 12 12 16 14"></polyline>
    </svg>"""
    cost = 5

    @classmethod
    def can_use(cls, team, task=None, tasksolution=None):
        """Check if Time Machine can be used"""
        from .models import Settings, TeamPowerUsage, ShopPower, TeamPurchase

        if not task or not tasksolution:
            return False, "Invalid task or solution"

        # Check if team has purchased it
        try:
            power = ShopPower.objects.get(power_type=cls.power_type, is_active=True)
            has_purchased = TeamPurchase.objects.filter(team=team, power=power).exists()

            if not has_purchased:
                return False, "You haven't purchased the Time Machine power"
        except ShopPower.DoesNotExist:
            return False, "Time Machine power is not available"

        # Check if already used on this task
        already_used = TeamPowerUsage.objects.filter(
            team=team, power=power, task=task
        ).exists()

        if already_used:
            return False, "You've already used Time Machine on this task"

        # Check if max attempts reached
        settings = Settings.get_settings()
        if tasksolution.attempts < settings.max_attempts:
            return (
                False,
                "You still have attempts remaining. Time Machine can only be used when you've reached max attempts.",
            )

        return True, "Ready to use"

    @classmethod
    def use(cls, team, task=None, tasksolution=None):
        """Use Time Machine to restore one attempt"""
        from .models import TeamPowerUsage, ShopPower

        # Validate usage
        can_use, reason = cls.can_use(team, task, tasksolution)
        if not can_use:
            return False, reason

        try:
            with transaction.atomic():
                # Get the power
                power = ShopPower.objects.get(power_type=cls.power_type, is_active=True)

                # Decrement attempts by 1
                tasksolution.attempts -= 1
                tasksolution.save()

                # Record usage
                TeamPowerUsage.objects.create(team=team, power=power, task=task)

                logger.info(f"Team {team.name} used Time Machine on task {task.id}")
                return (
                    True,
                    "⏰ Time Machine activated! You've been granted one extra attempt!",
                )

        except Exception as e:
            logger.error(f"Error using Time Machine: {str(e)}", exc_info=True)
            return False, "Error activating Time Machine. Please try again."


# TODO: x2 Points for the next submission (if the submission is successful)
# TODO: x1.5 Score for the next submission it can help to improve the submission score


# Registry of all available powers
POWER_HANDLERS = {
    "time_machine": TimeMachinePower,
}


def get_power_handler(power_type):
    """Get the handler class for a power type"""
    return POWER_HANDLERS.get(power_type)


def get_all_powers_info():
    """Get metadata for all available powers"""
    return [handler.get_power_info() for handler in POWER_HANDLERS.values()]


def sync_powers_to_db():
    """
    Sync power definitions from code to database.
    This ensures the database has all powers defined in code.
    """
    from .models import ShopPower

    for power_type, handler in POWER_HANDLERS.items():
        info = handler.get_power_info()
        ShopPower.objects.update_or_create(
            power_type=power_type,
            defaults={
                "name": info["name"],
                "description": info["description"],
                "icon": info["icon"],
                "cost": info["cost"],
                "is_active": True,
            },
        )

    logger.info(f"Synced {len(POWER_HANDLERS)} powers to database")
