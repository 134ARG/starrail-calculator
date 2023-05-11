import copy
import json
import types

class Entity:
    def __init__(self):
        self._attack = 0
        self._defence = 0
        self._critical_ratio = 0
        self._critical_damage = 0
        self._resistence = {
            "quantum":0,
            "fire":0,
            "wind":0,
            "lighting":0,
            "imaginary":0,
            "physical":0,
            "ice":0,
            }
        self._level = 0

    def toJson(self):
        pass

    def setATK(self, atk):
        self._attack = atk

    def getATK(self):
        return self._attack

    def setDEF(self, defence):
        self._defence = defence

    def getDEF(self):
        return self._defence

    def setCritRatio(self, ratio):
        self._critical_ratio = ratio

    def getCritRatio(self):
        return self._critical_ratio

    def setCritDamage(self, damage):
        self._critical_damage = damage

    def getCritDamage(self):
        return self._critical_damage

    def setResistence(self, res: dict):
        for e, v in res.items():
            self._resistence[e] = v

    def getResistence(self):
        return self._resistence

    def setLevel(self, level):
        self._level = level

    def getLevel(self):
        return self._level


class Monster(Entity):
    def __init__(self, atk, resistence, level, defence=None):
        super().__init__()
        self.setATK(atk)
        self.setResistence(resistence)
        self.setLevel(level)
        if defence is not None:
            self.setDEF(defence)
        else:
            self.setDEF(200+level*10)


class Character(Entity):
    def setElementType(self, element):
        self._element = element

    def getElementType(self):
        return self._element
    
    def setEleBoost(self, elemental_boost):
        self._elemental_boost = elemental_boost

    def getEleBoost(self):
        return self._elemental_boost

    def __init__(self, element, atk, defence, level, crit_ratio, crit_damage, elemental_boost):
        super().__init__()

        self._element = element
        self._elemental_boost = 0

        self.setATK(atk)
        self.setDEF(defence)
        self.setLevel(level)
        self.setCritRatio(crit_ratio)
        self.setCritDamage(crit_damage)
        self.setEleBoost(elemental_boost)


class CharacterDamage:
    def __init__(self, attacker: Character, attackee: Entity, scaling):
        self._attacker = attacker
        self._attackee = attackee

        self._scaling_value = scaling
        self._attack = attacker.getATK()

        self._element = attacker.getElementType()

        self._critical_damage = attacker.getCritDamage()
        self._critical_ratio = attacker.getCritRatio()
        self._critical_multiplier = 0

        # defence part
        self._defence_penetration = 0
        self._defence_multiplier = 0

        # resistence part
        self._resistence_penetration = 0
        self._resistence_multiplier = 0

        # bonus part
        self._damage_bonus_multiplier = 1
        self._incoming_damage_bonus_multiplier = 1

        self._prev_damage = 0
        self._increase_factor = 0

        self._damage_decrease_multiplier = 1

        self._fillCritical()
        self._fillResistence()
        self._fillDefence()

    def _fillCritical(self, specify_crit_ratio=None):
        if specify_crit_ratio is not None:
            self._critical_ratio = specify_crit_ratio
        self._critical_multiplier = 1 - self._critical_ratio + self._critical_ratio * \
            (1 + self._critical_damage)

    def _fillResistence(self):
        self._resistence_multiplier = 1.0 - \
            self._attackee.getResistence()[self._element] + \
            self._resistence_penetration

    def _fillDefence(self):
        level_val = 200 + 10*self._attacker.getLevel()
        penetrationFactor = 1 - self._defence_penetration
        if penetrationFactor < 0:
            penetrationFactor = 0
        self._defence_multiplier = level_val / \
            (penetrationFactor * self._attackee.getDEF()+level_val)

    def _getDefence(self, multiplier: float) -> float:
        level_val = 200 + 10*self._attacker.getLevel()
        penetrationFactor = 1 - self._defence_penetration
        if penetrationFactor < 0:
            penetrationFactor = 0
        return (level_val / multiplier - level_val) / penetrationFactor

    def _copy(self):
        new = copy.copy(self)
        new._prev_damage = self.report()
        return new
    
    def _getIncreaseFactor(self):
        if self._prev_damage != 0:
            self._increase_factor = self.report() / self._prev_damage
        else:
            self._increase_factor = 0

    def setScale(self, scaling):
        if scaling <= 0:
            raise ValueError("Improprite scaling value")
        self._scaling_value = scaling
        return self
    
    def setAttackee(self, attackee):
        self._attackee = attackee
        self._fillResistence()
        self._fillDefence()
        return self
    
    def addCritDamage(self, damage):
        newDamage = self._copy()
        newDamage._critical_damage += damage
        newDamage._fillCritical()
        newDamage._getIncreaseFactor()
        return newDamage

    def addDamageBonus(self, bonus):
        newDamage = self._copy()
        newDamage._damage_bonus_multiplier += bonus
        newDamage._getIncreaseFactor()
        return newDamage

    def addIncomingDamageBonus(self, bonus):
        newDamage = self._copy()
        newDamage._incoming_damage_bonus_multiplier += bonus
        newDamage._getIncreaseFactor()
        return newDamage

    def addDamageDecrease(self, decrease):
        newDamage = self._copy()
        newDamage._damage_decrease_multiplier -= decrease
        newDamage._getIncreaseFactor()
        return newDamage

    def addResistencePenetration(self, penetration):
        newDamage = self._copy()
        newDamage._resistence_penetration += penetration
        newDamage._fillResistence()
        newDamage._getIncreaseFactor()
        return newDamage

    def addDefencePenetration(self, penetration):
        newDamage = self._copy()
        newDamage._defence_penetration += penetration
        newDamage._fillDefence()
        newDamage._getIncreaseFactor()
        return newDamage
    
    def addBasicBonus(self, withWeaknessBreak=False):
        breakFactor = 1
        if withWeaknessBreak is True:
            breakFactor = 0
        return self.addDamageBonus(self._attacker.getEleBoost()).addDamageDecrease(breakFactor*0.1)

    def setToAlwaysCritical(self):
        newDamage = self._copy()
        newDamage._fillCritical(specify_crit_ratio=1.0)
        newDamage._getIncreaseFactor()
        return newDamage

    def setToNoCritical(self):
        newDamage = self._copy()
        newDamage._fillCritical(specify_crit_ratio=0.0)
        newDamage._getIncreaseFactor()
        return newDamage

    def getDefenceFromDamage(self, damage: float) -> float:
        defence_multiplier = damage / (self._attack * self._scaling_value * self._resistence_multiplier * self._critical_multiplier *
                                       self._damage_bonus_multiplier * self._incoming_damage_bonus_multiplier * self._damage_decrease_multiplier)
        defence = self._getDefence(defence_multiplier)
        return defence

    def report(self):
        return self._attack * self._scaling_value * self._defence_multiplier * self._resistence_multiplier * self._critical_multiplier * self._damage_bonus_multiplier * self._incoming_damage_bonus_multiplier * self._damage_decrease_multiplier

    def reportIncreaseFactor(self):
        return self._increase_factor
    
    def reportCrucialFactors(self):
        return {
            "scaling": self._scaling_value,
            "attack": self._attack,
            "critical_ratio": self._critical_ratio,
            "critical_damage": self._critical_damage,
            "critical_multiplier": self._critical_multiplier,
            "defence_multiplier": self._defence_multiplier,
            "resistence_multiplier": self._resistence_multiplier,
            "damage_bonus_multiplier": self._damage_bonus_multiplier,
            "incoming_damage_bonus_multiplier": self._incoming_damage_bonus_multiplier,
            "damage_decrease_multiplier": self._damage_decrease_multiplier
            }


# Example
class SeeleDamage(CharacterDamage):
    def addLecerate(self):
        return self.addResistencePenetration(0.2)

    def addBufferedBonus(self):
        return self.addDamageBonus(0.6)
    

class Seele(Character):
    def __init__(self, atk, defence, level, crit_ratio, crit_damage, elemental_boost):
        super().__init__("quantum", atk, defence, level, crit_ratio, crit_damage, elemental_boost)

    def baseUltimate(self, target: Entity, scaling: float, with_weakness_break=False) -> CharacterDamage:
        return SeeleDamage(self, target, scaling).addBasicBonus(with_weakness_break).addBufferedBonus().addLecerate()

    def baseSkill(self, target: Entity, scaling: float, with_weakness_break=False) -> CharacterDamage:
        return SeeleDamage(self, target, scaling).addBasicBonus(with_weakness_break)


cocolia = Monster(0, {"quantum": 0, "wind": 0.4, "physical": 0.4}, 57)
antimatterengine = Monster(0, {"quantum":0.4}, 57, defence=768)

def triggerFullQuantumSuitAndInTheNight(d:CharacterDamage):
    return d.addDefencePenetration(0.2).addCritDamage(0.72)

def tiggerPelaUltimate(d:CharacterDamage):
    return d.addDefencePenetration(0.35)

# salsotto pair with quantum suit
seele = Seele(atk=2205, defence=0, level=60, crit_ratio=0.726, crit_damage=0.84, elemental_boost=0.488)
seeleUltimateWithSalsotto = seele.baseUltimate(cocolia, 3.4, with_weakness_break=False).addDamageBonus(0.15)

d = triggerFullQuantumSuitAndInTheNight(seeleUltimateWithSalsotto)

print("damage to cocolia with Salsotto", d.report())
print(d.reportCrucialFactors())

# space station pair with quantum suit
seele2 = Seele(atk=(2205+901*0.24), defence=0, level=60, crit_ratio=0.646, crit_damage=0.84, elemental_boost=0.488)
seeleUltimateWithStation = seele2.baseUltimate(cocolia, 3.4, with_weakness_break=False)

d = triggerFullQuantumSuitAndInTheNight(seeleUltimateWithStation)

print("damage to cocolia with station suit", d.report())
print(d.reportCrucialFactors())

