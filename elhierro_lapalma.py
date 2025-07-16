"""
Hotel Cost Calculator for Paradores El Hierro and La Palma
Calculates optimal room allocation and price per person.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple
from enum import Enum

# Global configuration
NIGHTS = 5
MEALS_PER_DAY = 3  # Breakfast, lunch, dinner
MEAL_COST_PER_PERSON = 38  # € per meal per person
MEETING_ROOM_DAYS = 4  # Number of days meeting room is rented


class RoomCategory(Enum):
    STANDARD = "standard"
    SUPERIOR = "superior"


class OccupancyType(Enum):
    SHARED = "shared"
    SINGLE = "single"


@dataclass
class RoomRate:
    """Room pricing information"""
    shared_rate: float  # € per room when 2 people share
    single_rate: float  # € per room when 1 person occupies


@dataclass
class RoomInventory:
    """Maximum available rooms by category"""
    standard_count: int
    superior_count: int


@dataclass
class RoomAllocation:
    """How rooms are allocated for a group"""
    standard_shared: int = 0
    standard_single: int = 0
    superior_shared: int = 0
    superior_single: int = 0
    
    def get_total_cost(self, rates: HotelRates) -> float:
        """Calculate total cost for this allocation for the entire stay"""
        daily_cost = (
            self.standard_shared * rates.standard.shared_rate +
            self.standard_single * rates.standard.single_rate +
            self.superior_shared * rates.superior.shared_rate +
            self.superior_single * rates.superior.single_rate
        )
        return daily_cost * NIGHTS
    
    def get_total_rooms_used(self) -> int:
        """Get total number of rooms used"""
        return (self.standard_shared + self.standard_single + 
                self.superior_shared + self.superior_single)


@dataclass
class HotelRates:
    """Pricing for a hotel"""
    standard: RoomRate
    superior: RoomRate


@dataclass
class HotelConfig:
    """Complete hotel configuration"""
    name: str
    inventory: RoomInventory
    rates: HotelRates
    coffee_break_cost: float  # € per coffee break per person
    meeting_room_cost: float  # € total cost for meeting room rental
    
    def get_max_capacity(self) -> int:
        """Maximum number of people the hotel can accommodate"""
        return (self.inventory.standard_count * 2 + 
                self.inventory.superior_count * 2)


class HotelAllocator:
    """Handles room allocation logic"""
    
    def __init__(self, config: HotelConfig):
        self.config = config
    
    def allocate_rooms(self, num_people: int) -> RoomAllocation:
        """
        Allocate people to rooms optimally.
        Prioritizes shared rooms and standard over superior.
        """
        if num_people > self.config.get_max_capacity():
            raise ValueError(f"Group size {num_people} exceeds hotel maximum capacity {self.config.get_max_capacity()}")
        
        allocation = RoomAllocation()
        people_remaining = num_people
        
        # Step 1: Fill shared rooms (prefer standard over superior)
        people_remaining = self._allocate_shared_rooms(allocation, people_remaining)
        
        # Step 2: Fill single rooms for remaining people
        people_remaining = self._allocate_single_rooms(allocation, people_remaining)
        
        if people_remaining > 0:
            raise ValueError("Failed to allocate all people to rooms")
        
        return allocation
    
    def _allocate_shared_rooms(self, allocation: RoomAllocation, people_remaining: int) -> int:
        """Allocate people to shared rooms, preferring cheapest rooms first"""
        # Calculate cost per person for each room type when shared
        room_costs = [
            (self.config.rates.standard.shared_rate / 2, "standard"),  # €79 per person
            (self.config.rates.superior.shared_rate / 2, "superior"),  # €90.5 per person
        ]
        
        # Sort by cost per person (cheapest first)
        room_costs.sort()
        
        for cost_per_person, room_type in room_costs:
            if people_remaining <= 0:
                break
                
            if room_type == "standard":
                rooms_available = self.config.inventory.standard_count - allocation.standard_shared
                rooms_to_use = min(rooms_available, people_remaining // 2)
                allocation.standard_shared = rooms_to_use
                people_remaining -= rooms_to_use * 2
            else:  # superior
                rooms_available = self.config.inventory.superior_count - allocation.superior_shared
                rooms_to_use = min(rooms_available, people_remaining // 2)
                allocation.superior_shared = rooms_to_use
                people_remaining -= rooms_to_use * 2
        
        return people_remaining
    
    def _allocate_single_rooms(self, allocation: RoomAllocation, people_remaining: int) -> int:
        """Allocate remaining people to single rooms, preferring cheapest rooms first"""
        # Calculate cost per person for each room type when used singly
        room_costs = [
            (self.config.rates.standard.single_rate, "standard"),  # €136 per person
            (self.config.rates.superior.single_rate, "superior"),  # €159 per person
        ]
        
        # Sort by cost per person (cheapest first)
        room_costs.sort()
        
        for cost_per_person, room_type in room_costs:
            if people_remaining <= 0:
                break
                
            if room_type == "standard":
                rooms_available = (self.config.inventory.standard_count - 
                                 allocation.standard_shared - allocation.standard_single)
                rooms_to_use = min(rooms_available, people_remaining)
                allocation.standard_single = rooms_to_use
                people_remaining -= rooms_to_use
            else:  # superior
                rooms_available = (self.config.inventory.superior_count - 
                                 allocation.superior_shared - allocation.superior_single)
                rooms_to_use = min(rooms_available, people_remaining)
                allocation.superior_single = rooms_to_use
                people_remaining -= rooms_to_use
        
        return people_remaining


class HotelCostCalculator:
    """Main calculator class"""
    
    def __init__(self):
        self.hotels = self._initialize_hotels()
    
    def _initialize_hotels(self) -> Dict[str, HotelConfig]:
        """Initialize hotel configurations with maximum room availability"""
        return {
            "el_hierro": HotelConfig(
                name="Parador de El Hierro",
                inventory=RoomInventory(standard_count=20, superior_count=20),  # Max availability
                rates=HotelRates(
                    standard=RoomRate(shared_rate=158, single_rate=136),
                    superior=RoomRate(shared_rate=181, single_rate=159)
                ),
                coffee_break_cost=7,  # € per coffee break
                meeting_room_cost=200  # € total for meeting room
            ),
            "la_palma": HotelConfig(
                name="Parador de La Palma", 
                inventory=RoomInventory(standard_count=21, superior_count=24),  # Max availability
                rates=HotelRates(
                    standard=RoomRate(shared_rate=164, single_rate=144),
                    superior=RoomRate(shared_rate=186, single_rate=166)
                ),
                coffee_break_cost=8,  # € per coffee break
                meeting_room_cost=800  # € total for meeting room
            )
        }
    
    def calculate_accommodation_cost(self, num_people: int, hotel_key: str) -> float:
        """Calculate accommodation cost per person for the entire stay"""
        if hotel_key not in self.hotels:
            raise ValueError(f"Unknown hotel: {hotel_key}")
        
        config = self.hotels[hotel_key]
        allocator = HotelAllocator(config)
        allocation = allocator.allocate_rooms(num_people)
        
        total_accommodation_cost = allocation.get_total_cost(config.rates)
        return total_accommodation_cost / num_people
    
    def calculate_meal_cost(self) -> float:
        """Calculate meal cost per person for the entire stay"""
        # First day: 1 meal (dinner)
        # Middle days: 3 meals per day (breakfast, lunch, dinner)
        # Last day: 1 meal (breakfast)
        # Total meals = 1 + (3 * (NIGHTS - 2)) + 1 = 1 + 3*(NIGHTS-2) + 1 = 2 + 3*(NIGHTS-2)
        total_meals_per_person = 1 + (3 * (NIGHTS - 2)) + 1
        return total_meals_per_person * MEAL_COST_PER_PERSON
    
    def calculate_coffee_break_cost(self, hotel_key: str) -> float:
        """Calculate coffee break cost per person for the entire stay"""
        if hotel_key not in self.hotels:
            raise ValueError(f"Unknown hotel: {hotel_key}")
        
        config = self.hotels[hotel_key]
        # Coffee breaks only on middle days (N-2 days), 2 per day
        # First day: no coffee breaks (people arrive)
        # Middle days: 2 coffee breaks per day
        # Last day: no coffee breaks (people leave)
        coffee_breaks_per_person = 2 * (NIGHTS - 2)
        return coffee_breaks_per_person * config.coffee_break_cost
    
    def calculate_meeting_room_cost(self, num_people: int, hotel_key: str) -> float:
        """Calculate meeting room cost per person for the entire stay"""
        if hotel_key not in self.hotels:
            raise ValueError(f"Unknown hotel: {hotel_key}")
        
        config = self.hotels[hotel_key]
        # Total meeting room cost divided by number of people
        return config.meeting_room_cost / num_people
    
    def calculate_total_price_per_person(self, num_people: int, hotel_key: str) -> float:
        """Calculate total price per person (accommodation + meals + coffee breaks + meeting room) for the entire stay"""
        accommodation_cost = self.calculate_accommodation_cost(num_people, hotel_key)
        meal_cost = self.calculate_meal_cost()
        coffee_break_cost = self.calculate_coffee_break_cost(hotel_key)
        meeting_room_cost = self.calculate_meeting_room_cost(num_people, hotel_key)
        return accommodation_cost + meal_cost + coffee_break_cost + meeting_room_cost
    
    def get_detailed_allocation(self, num_people: int, hotel_key: str) -> Tuple[RoomAllocation, float, float, float, float]:
        """Get detailed room allocation, accommodation cost, meal cost, coffee break cost, and meeting room cost for the entire stay"""
        if hotel_key not in self.hotels:
            raise ValueError(f"Unknown hotel: {hotel_key}")
        
        config = self.hotels[hotel_key]
        allocator = HotelAllocator(config)
        allocation = allocator.allocate_rooms(num_people)
        
        total_accommodation_cost = allocation.get_total_cost(config.rates)
        total_meal_cost = self.calculate_meal_cost() * num_people
        total_coffee_break_cost = self.calculate_coffee_break_cost(hotel_key) * num_people
        total_meeting_room_cost = self.calculate_meeting_room_cost(num_people, hotel_key) * num_people
        
        return allocation, total_accommodation_cost, total_meal_cost, total_coffee_break_cost, total_meeting_room_cost
    
    def print_comparison(self, group_sizes: List[int] = None) -> None:
        """Print price comparison for different group sizes"""
        if group_sizes is None:
            #group_sizes = list(range(30, 50))
            group_sizes = [30,40,50]
        
        for hotel_key, config in self.hotels.items():
            print(f"\n{'='*120}")
            print(f"{config.name}")
            print(f"{'='*120}")
            print(f"Stay Duration: {NIGHTS} nights")
            print(f"Meals: Day 1 (dinner), middle days (3 meals), last day (breakfast) ({MEAL_COST_PER_PERSON}€ each)")
            print(f"Coffee Breaks: 2 per day on middle days ({config.coffee_break_cost}€ each)")
            print(f"Meeting Room: {MEETING_ROOM_DAYS} days ({config.meeting_room_cost}€ total, divided by group size)")
            print(f"Maximum Capacity: {config.get_max_capacity()} people")
            print(f"Room Availability: {config.inventory.standard_count} standard, {config.inventory.superior_count} superior")
            print(f"{'Group Size':>12} {'Accommodation/Person':>20} {'Meals/Person':>15} {'Coffee/Person':>15} {'Meeting/Person':>15} {'Total/Person':>15} {'TOTAL':>15}")
            print("-" * 120)
            
            for num_people in group_sizes:
                try:
                    accommodation_per_person = self.calculate_accommodation_cost(num_people, hotel_key)
                    meals_per_person = self.calculate_meal_cost()
                    coffee_per_person = self.calculate_coffee_break_cost(hotel_key)
                    meeting_per_person = self.calculate_meeting_room_cost(num_people, hotel_key)
                    total_per_person = accommodation_per_person + meals_per_person + coffee_per_person + meeting_per_person
                    total_cost = total_per_person * num_people
                    print(f"{num_people:>12} {accommodation_per_person:>20.0f}€ {meals_per_person:>15.0f}€ {coffee_per_person:>15.0f}€ {meeting_per_person:>15.0f}€ {total_per_person:>15.0f}€ {total_cost:>15.0f}€")
                except ValueError as e:
                    print(f"{num_people:>12} {'N/A':>20} {'N/A':>15} {'N/A':>15} {'N/A':>15} {'N/A':>15} {'N/A':>15} ({e})")


def main():
    """Main function to run the calculator"""
    calculator = HotelCostCalculator()
    calculator.print_comparison()


if __name__ == "__main__":
    main()