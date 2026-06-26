from aiogram.fsm.state import State, StatesGroup

class CostQuiz(StatesGroup):
    choosing_car_category = State()
    choosing_service = State()
    waiting_for_booking_decision = State()

class DiscountBooking(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_date = State()
    waiting_for_time = State()