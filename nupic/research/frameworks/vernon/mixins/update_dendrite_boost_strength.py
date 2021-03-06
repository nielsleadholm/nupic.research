# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2021, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------


from nupic.research.frameworks.dendrites import (
    BoostedDendritesBase,
    update_dendrite_boost_stregth,
)

__all__ = [
    "UpdateDendriteBoostStrength"
]


class UpdateDendriteBoostStrength:
    """
    Update the BoostedDendrites boost strength before every epoch.
    """
    def pre_epoch(self):
        """Apply update boost strength."""
        super().pre_epoch()
        self.model.apply(update_dendrite_boost_stregth)

    def run_epoch(self):
        """Log the boost strength to the results."""

        results = super().run_epoch()
        for name, module in self.model.named_modules():
            if isinstance(module, BoostedDendritesBase):
                results.update({
                    f"boost_strength/{name}": module.boost_strength.item()
                })

        return results

    @classmethod
    def get_execution_order(cls):
        eo = super().get_execution_order()
        name = "UpdateDendriteBoostStrength: "
        eo["pre_epoch"].append(name + "Update boost strength.")
        eo["run_epoch"].append(name + "Record boost strength.")
        return eo
