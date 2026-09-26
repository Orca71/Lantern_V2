#Abstract base class for all database adapters
#Defines the contract which every adapter must follow
#New adapter types like SaaS, Retail and etc will inherit this class as their foundation

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from abc import abstractmethod, ABC

class BaseAdapter(ABC):
    def __init__(self, db_path:str):
        """
        Args:
            db_path: path to sqlite database file
        """
        self.db_path = Path(db_path)
        self.mapping = {}
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

# Abstract methods, every subclass must implement these
    @abstractmethod
    def inspect_schema(self) -> dict:
        """
        Read the real database schema.
        Returns: {table_name : [column_info_dicts]}
        """
        raise NotImplementedError

    @abstractmethod
    def suggest_mappings(self, schema: dict) -> dict:
        """
        Give a real schema, suggest canonical mapping
        using the synonym dictionary
        Returns: {canonical_table: {canonical_col: real_col}}
        """
        raise NotImplementedError

    @abstractmethod
    def validate_mapping(self, mapping: dict) -> list[str]:
        """
        Confirm every field Lantern needs resolves through the mapping. Returns a list of error strings.
        Empty list means the mapping valid.
        """
        raise NotImplementedError

    @abstractmethod
    def generate_views(self, mapping: dict) -> list[str]:
        """
        Generate CREATE VIEW SQL statements from the mapping.
        Returns list of SQL strings ready to execute
        """
        raise NotImplementedError


#Methods shared by all subclasses

    def get_business_type(self) -> str:
        """Returns the busniess type identifier for this adapter."""
        return self.__class__.__name__.replace("Adapter", "").lower()

    def is_ready(self) -> bool:
        """
        Returns True if a validated mapping exists.
        Used bu the registry to check if setup is complete.
        """
        return bool(self.mapping)
