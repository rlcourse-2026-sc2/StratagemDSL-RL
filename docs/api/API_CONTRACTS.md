# StratagemDSL API contracts

Signatures come from the same registry as the type checker and LLM tool schema. `lowered` describes an existing compiler mapping, not a proven runtime outcome. Agent-side actions remain strategic intent.

## Predicates and metrics

| API / signature | Backend | Galaxy mapping | Preconditions | Order evidence | Effect evidence | Actor |
| --- | --- | --- | --- | --- | --- | --- |
| `ability_charge_regen_left(Entity, String, String) -> Float` | lowered | v04 registry mapping: ability_charge_regen_left | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `ability_charges_used(Entity, String, String) -> Float` | lowered | v04 registry mapping: ability_charges_used | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `ability_count(String, String) -> Int` | lowered | v04 registry mapping: ability_count | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `ability_enabled(Entity, String) -> Bool` | lowered | v04 registry mapping: ability_enabled | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `ability_level(Entity, String) -> Float` | lowered | v04 registry mapping: ability_level | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `active(Any) -> Bool` | lowered | gv_net_m_<place> > 0 | plan place or phase name; true while it holds a token |  | exact current marking | none |
| `after(Number) -> Bool` | lowered | GameGetMissionTime() >= seconds | nonnegative absolute mission-time threshold; eventless transition polls every 1s |  | deadline reached, even when phase starts after deadline | none |
| `airborne(Entity) -> Bool` | lowered | v04 registry mapping: airborne | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `alive(Entity) -> Bool` | lowered | UnitGroupCount(group, alive)>0 | bound entity |  | live group membership | none |
| `allied(String, String) -> Bool` | lowered | v04 registry mapping: allied | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `apparent_count(Force) -> Int` (alias: `player_unit_count`) | lowered | UnitGroupCount(UnitGroup(null, owner, entire map, default filter), alive) | compatibility alias; prefer player_unit_count |  | owner-wide live units matching default filter, not observer-visible count | none |
| `army_value(Entity) -> Int` | lowered | v04 registry mapping: army_value | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `at(Entity, Location) -> Bool` | unsupported | none | use in_region(force, circle) for a concrete guard |  |  | none |
| `bearing(Entity, Entity) -> Float`, `bearing(Entity, Region) -> Float` | lowered | v04 registry mapping: bearing | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `can_attack(Force, Entity) -> Bool` | lowered | v04 registry mapping: can_attack | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `can_reach(Force, Entity) -> Bool`, `can_reach(Force, Region) -> Bool` | lowered | v04 registry mapping: can_reach | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `cargo_count(Entity) -> Int` | lowered | v04 registry mapping: cargo_count | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `cargo_space(Entity) -> Int` | lowered | v04 registry mapping: cargo_space | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `carried(Entity) -> Bool` | lowered | v04 registry mapping: carried | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `carried_by(Entity, Entity) -> Bool` | lowered | v04 registry mapping: carried_by | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `center_passable(Region) -> Bool` | lowered | PointPathingPassable(region.center) | circle region with a point center |  | center point passable; does not prove route reachability | none |
| `charge_regen_left(Entity, String) -> Float` | lowered | v04 registry mapping: charge_regen_left | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `charges_used(Entity, String) -> Float` | lowered | v04 registry mapping: charges_used | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `chosen(String, String) -> Bool` | lowered | v04 registry mapping: chosen | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `combat_power(Force) -> Float` | lowered | v04 registry mapping: combat_power | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `construction_complete(Asset) -> Bool` | lowered | live singleton group AND !libNtve_gf_UnitIsUnderConstruction(UnitGroupUnit(group,1)) | asset must bind one stable unit; returns false when dead |  | current live unit is no longer under construction | none |
| `cooldown_left(Entity, String) -> Float` | lowered | v04 registry mapping: cooldown_left | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `count(Force) -> Int` | lowered | UnitGroupCount(bound force, alive) | bound force |  | live units in this exact bound group | none |
| `count_in(Force, Region) -> Int` | lowered | UnitGroupCount(UnitGroupFilterRegion(...), alive) | bound force and circle |  | live bound members in region | none |
| `count_matching(Entity, String) -> Int` | lowered | UnitFilterMatch over alive bound members | validated filter names |  |  | none |
| `count_matching_vs(Entity, String, String) -> Int` | lowered | v04 registry mapping: count_matching_vs | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `count_owned(Entity, String) -> Int` | lowered | v04 registry mapping: count_owned | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `count_snapshot(String) -> Int` | lowered | v04 registry mapping: count_snapshot | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `count_tagged(Entity, String, Number) -> Int` | lowered | v04 registry mapping: count_tagged | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `creep_adjacent(Region) -> Int` | lowered | v04 registry mapping: creep_adjacent | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `creep_available(Region) -> Bool` | lowered | CreepIsPresent(region.center) | circle region with point center |  | creep at center point | none |
| `damage_from(Entity, Entity) -> Int` | lowered | v04 registry mapping: damage_from | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `damaged_by(Entity, Entity, Number) -> Bool` | lowered | v04 registry mapping: damaged_by | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `damaged_with(Entity, String) -> Bool` | lowered | v04 registry mapping: damaged_with | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `defeated(Force) -> Bool` | lowered | UnitGroupCount(group, alive)==0 | bound force |  | no live group member | none |
| `defense_weakened(Asset) -> Bool` | strategic_only | none | pattern inference is plan evidence, not a runtime observation |  | use count_in or other observable proof | none |
| `destroyed(Entity) -> Bool` | lowered | UnitGroupCount(group, alive)==0 | bound entity |  | no live group member | none |
| `distance(Entity, Entity) -> Float` | lowered | DistanceBetweenPoints(group center, group center) | both live; strict guard requires explicit alive conjuncts |  | distance of current group centers | none |
| `elapsed(Any) -> Float` | lowered | GameGetMissionTime() - phase entry time | phase name; entry-relative game seconds |  |  | none |
| `engaging(Entity) -> Bool` | lowered | v04 registry mapping: engaging | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `event_ability_is(String) -> Bool` | special_context | v04 registry mapping: event_ability_is | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `event_amount() -> Float` | special_context | event-specific numeric amount | matching event context only |  |  | none |
| `event_cargo_in(Entity) -> Bool` | special_context | v04 registry mapping: event_cargo_in | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `event_created_by(String) -> Bool` | special_context | v04 registry mapping: event_created_by | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `event_created_by_status(String) -> Bool` | special_context | v04 registry mapping: event_created_by_status | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `event_damage(String) -> Float` | special_context | v04 registry mapping: event_damage | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `event_death_is(String) -> Bool` | special_context | v04 registry mapping: event_death_is | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `event_effect_is(String) -> Bool` | special_context | v04 registry mapping: event_effect_is | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `event_in(Region) -> Bool` | special_context | event subject within bound region | unit event only |  |  | none |
| `event_leeched(String) -> Float` | special_context | v04 registry mapping: event_leeched | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `event_object_is(String) -> Bool` | special_context | v04 registry mapping: event_object_is | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `event_other_in(Entity) -> Bool` | special_context | v04 registry mapping: event_other_in | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `event_product_in(Entity) -> Bool` | special_context | v04 registry mapping: event_product_in | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `event_source_at(Region) -> Bool` | special_context | v04 registry mapping: event_source_at | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `event_source_in(Entity) -> Bool` | special_context | event-specific source unit membership | matching event context only |  |  | none |
| `event_source_side(String) -> Bool` | special_context | v04 registry mapping: event_source_side | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `event_stage_is(String) -> Bool` | special_context | v04 registry mapping: event_stage_is | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `event_target_in(Entity) -> Bool` | special_context | event-specific target unit membership | matching event context only |  |  | none |
| `event_vital_is(String) -> Bool` | special_context | v04 registry mapping: event_vital_is | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `event_weapon_is(String) -> Bool` | special_context | v04 registry mapping: event_weapon_is | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `firepower(Force) -> Float` | lowered | v04 registry mapping: firepower | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `flank_angle(Entity, Entity, Entity) -> Float` | lowered | v04 registry mapping: flank_angle | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `has_ability(Entity, String) -> Bool` | lowered | v04 registry mapping: has_ability | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `has_addon(Entity) -> Bool` | lowered | v04 registry mapping: has_addon | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `has_status(Entity, String) -> Bool` | lowered | any live member has behavior | game-data behavior link |  |  | none |
| `hostile(String, String) -> Bool` | lowered | v04 registry mapping: hostile | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `hostile_mutual(String, String) -> Bool` | lowered | v04 registry mapping: hostile_mutual | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `idle_count(Entity) -> Int` | lowered | v04 registry mapping: idle_count | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `in_region(Entity, Region) -> Bool` | lowered | UnitGroupFilterRegion + UnitGroupCount > 0 | circle region and bound force/asset |  | at least one live unit in region | none |
| `invulnerable(Entity) -> Bool` | lowered | v04 registry mapping: invulnerable | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `killed_in(Force, Region) -> Int` | special_context | unit_died monitor + deduplicated counter | circle; in guards use a comparison such as killed_in(f,r)>=3 |  | cumulative deduplicated death count in region | none |
| `known(String) -> Bool` | lowered | v04 registry mapping: known | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `life_ratio(Entity) -> Float` | lowered | sum current life / sum maximum life | alive members; empty group returns zero |  |  | none |
| `marked(String) -> Bool` | lowered | v04 registry mapping: marked | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `mission_time() -> Float` | lowered | GameGetMissionTime() | game-time seconds since mission start, not time since phase entry |  | current mission clock | none |
| `mode_is(Entity, String) -> Bool` | unsupported | none | ability order is not mode state |  |  | none |
| `near_remembered(Entity, String, Number) -> Bool` | lowered | v04 registry mapping: near_remembered | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `nearest_distance(Entity, Entity) -> Float` | lowered | minimum live member pair distance | alive groups; no pairs return sentinel |  |  | none |
| `order_rejected(Force) -> Bool` | lowered | v04 registry mapping: order_rejected | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `ordered_with(Entity, String) -> Bool` | lowered | v04 registry mapping: ordered_with | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `path_connected(Region, Region) -> Bool` | lowered | PointPathingIsConnected(a.center, b.center) | two circle regions with point centers; ground pathing only |  | center-to-center ground connectivity, not unit-specific reachability | none |
| `path_passable(Region) -> Bool` (alias: `center_passable`) | lowered | PointPathingPassable(region.center) | compatibility alias; prefer center_passable |  | center point only, no path | none |
| `pathing_is(Region, String) -> Bool` | lowered | v04 registry mapping: pathing_is | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `player_unit_count(Force) -> Int` | lowered | UnitGroupCount(UnitGroup(null, owner, entire map, default filter), alive) | force binding with numeric owner |  | owner-wide live units matching default filter, not force roster or observer visibility | none |
| `powered(Entity) -> Bool` | lowered | v04 registry mapping: powered | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `powered_by(Entity, Entity) -> Bool` | lowered | v04 registry mapping: powered_by | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `producing(Entity) -> Bool` | lowered | v04 registry mapping: producing | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `queue_used(Entity) -> Int` | lowered | v04 registry mapping: queue_used | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `queued(Entity, String) -> Int` | lowered | v04 registry mapping: queued | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `race_is(String, String) -> Bool` | lowered | v04 registry mapping: race_is | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `rallied_to(Entity, Region) -> Bool` | lowered | v04 registry mapping: rallied_to | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `recall(String) -> Float` | lowered | v04 registry mapping: recall | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `relieved(Asset) -> Bool` | strategic_only | none | describe in intent/derive; ground a guard in observable state |  | no automatic proof of relief | none |
| `remembered_alive(String) -> Bool` | lowered | v04 registry mapping: remembered_alive | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `remembered_in(Entity, String) -> Bool` | lowered | v04 registry mapping: remembered_in | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `resources_left(Entity) -> Int` | lowered | v04 registry mapping: resources_left | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `retargeted(Force, Entity) -> Bool` | strategic_only | none | retarget order does not prove retargeting |  | no runtime retarget proof | none |
| `retreating(Force) -> Bool` | unsupported | none | no movement-state observer in backend |  |  | none |
| `score(String, String) -> Float` | lowered | v04 registry mapping: score | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `score_count(String, String) -> Int` | lowered | v04 registry mapping: score_count | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `shield_left(Entity, String) -> Float` | lowered | v04 registry mapping: shield_left | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `side_active(String) -> Bool` | lowered | v04 registry mapping: side_active | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `side_size(String) -> Int` | lowered | v04 registry mapping: side_size | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `snapshot_lost(String) -> Int` | lowered | v04 registry mapping: snapshot_lost | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `state(Entity, String) -> Bool` | lowered | v04 registry mapping: state | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `status_active(Entity, String) -> Bool` | lowered | v04 registry mapping: status_active | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `status_charge_regen_left(Entity, String, String) -> Float` | lowered | v04 registry mapping: status_charge_regen_left | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `status_charges_used(Entity, String, String) -> Float` | lowered | v04 registry mapping: status_charges_used | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `status_cooldown_left(Entity, String, String) -> Float` | lowered | v04 registry mapping: status_cooldown_left | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `status_count(String, String) -> Int` | lowered | v04 registry mapping: status_count | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `status_fraction_left(Entity, String) -> Float` | lowered | v04 registry mapping: status_fraction_left | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `status_source_in(Entity, String, Entity) -> Bool` | lowered | v04 registry mapping: status_source_in | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `status_source_side(Entity, String, String) -> Bool` | lowered | v04 registry mapping: status_source_side | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `strength(Force) -> Float` | unsupported | none | no unit-strength metric in backend |  |  | none |
| `summoned_by(Entity, Entity) -> Bool` | lowered | v04 registry mapping: summoned_by | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `summoned_with(Entity, String) -> Bool` | lowered | v04 registry mapping: summoned_with | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `supply(String, String) -> Float` | lowered | v04 registry mapping: supply | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `support_separated(Force, Entity) -> Bool` | unsupported | none | no separation observer in backend |  |  | none |
| `tallied(String) -> Int` | lowered | v04 registry mapping: tallied | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `targeting(Force, Entity) -> Bool`, `targeting(Force, Region) -> Bool` | lowered | current live unit order target | observable order target; does not establish damage |  | current command target only | none |
| `tech_allowed(String, String, String) -> Bool` | lowered | v04 registry mapping: tech_allowed | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `threatened(Asset) -> Bool` | unsupported | none | no threat observer in backend |  |  | none |
| `tokens(Any) -> Int` | lowered | marking global gv_net_m_<place> | plan place or phase name; reads the token count of the plan net |  | exact current marking | none |
| `train_progress(Entity) -> Float` | lowered | v04 registry mapping: train_progress | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `under_construction(Entity) -> Bool` | lowered | v04 registry mapping: under_construction | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `unit_status_count(Entity, String) -> Int` | lowered | v04 registry mapping: unit_status_count | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `unit_upgrade_count(Entity, String) -> Int` | lowered | v04 registry mapping: unit_upgrade_count | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `visible_to(String, Entity) -> Bool`, `visible_to(String, Region) -> Bool` | lowered | unit visibility or region-center visibility | single-player side; region query observes center |  |  | none |
| `window_held(Phase, Number) -> Bool` | lowered | v04 registry mapping: window_held | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |

## Transition events

| API / signature | Backend | Galaxy mapping | Preconditions | Order evidence | Effect evidence | Actor |
| --- | --- | --- | --- | --- | --- | --- |
| `ability_cast(Entity, String) -> Any`, `ability_cast(Force, String) -> Any` | lowered | TriggerAddEventUnitAbility(c_abilEffectStageCast) | ability identifier must match game's data; unit match |  | cast-stage event | none |
| `ability_completed(Entity, String) -> Any`, `ability_completed(Force, String) -> Any` | lowered | TriggerAddEventUnitAbility(c_unitAbilStageComplete) | ability identifier must match game's data; unit match |  | ability completion event | none |
| `ability_stage(Entity, String, String) -> Any` | lowered | v04 registry mapping: ability_stage | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `acquired_target(Entity) -> Any` | lowered | v04 registry mapping: acquired_target | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `attack_started(Entity) -> Any` | lowered | v04 registry mapping: attack_started | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `autocast_changed(Entity, String, String) -> Any` | lowered | v04 registry mapping: autocast_changed | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `construction_completed(Asset) -> Any` | lowered | TriggerAddEventUnitConstructProgress(c_unitProgressStageComplete) | bound asset |  | construction completion event | none |
| `damage_absorbed(Entity, String) -> Any` | lowered | v04 registry mapping: damage_absorbed | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `effect_used(Entity, String) -> Any` | lowered | TriggerAddEventEffectUsed + caster membership | game-data effect link |  |  | none |
| `enter(Force, Region) -> Any` | lowered | TriggerAddEventUnitRegion + EventUnit membership | bound force and circle |  | matching unit entered region | none |
| `leave(Force, Region) -> Any` | lowered | TriggerAddEventUnitRegion + EventUnit membership | bound force and circle |  | matching unit left region | none |
| `loaded(Entity) -> Any` | lowered | v04 registry mapping: loaded | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `produced(Entity, String) -> Any` | lowered | v04 registry mapping: produced | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `property_changed(String, String) -> Any` | lowered | v04 registry mapping: property_changed | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `research_done(Entity, String) -> Any` | lowered | v04 registry mapping: research_done | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `side_left(String) -> Any` | lowered | v04 registry mapping: side_left | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `status_class_gained(Entity, String) -> Any` | lowered | v04 registry mapping: status_class_gained | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `status_class_lost(Entity, String) -> Any` | lowered | v04 registry mapping: status_class_lost | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `timer(Any, Number) -> Any` | lowered | phase-local one-shot timer | phase name and positive duration; starts at entry |  |  | none |
| `trained(Entity, String) -> Any` | lowered | v04 registry mapping: trained | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `unit_attacked(Entity) -> Any`, `unit_attacked(Entity, Force) -> Any` | lowered | TriggerAddEventUnitAttacked2 + EventUnit + EventUnitTarget membership | bound victim; optional attacking force uses stable group identity |  | victim attacked by specified force; neither damage nor sustained targeting implied | none |
| `unit_became_idle(Force) -> Any` | lowered | TriggerAddEventUnitBecomesIdle(trigger,null,true) + EventUnit membership | event denotes one bound member becoming idle, not all group members |  | one member becomes idle; arrival and phase completion need separate conditions | none |
| `unit_damaged(Entity) -> Any` | lowered | TriggerAddEventUnitDamaged + victim membership | bound victim roster |  |  | none |
| `unit_died(Entity) -> Any`, `unit_died(Force) -> Any`, `unit_died(Entity, Force) -> Any` | lowered | TriggerAddEventUnitDied + EventUnit + libNtve_gf_KillingUnit membership | stable victim roster; optional killer force may be absent for environmental deaths |  | bound victim death and, when specified, killer membership observed | none |
| `unit_healed(Entity) -> Any` | lowered | v04 registry mapping: unit_healed | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `unloaded(Entity) -> Any` | lowered | v04 registry mapping: unloaded | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `upgrade_changed(String, String) -> Any` | lowered | v04 registry mapping: upgrade_changed | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |
| `vital_changed(Entity, String) -> Any` | lowered | v04 registry mapping: vital_changed | game-data links require engine validation |  | compiler mapping only; outcome requires observation | none |

## Plan actions

| API / signature | Backend | Galaxy mapping | Preconditions | Order evidence | Effect evidence | Actor |
| --- | --- | --- | --- | --- | --- | --- |
| `apply_effect(Entity, String, Entity) -> Any` | lowered | UnitCreateEffectUnit | script effect; game-data link validation remains external |  |  | environment |
| `attack(Force, Entity) -> Any`, `attack(Force, Force) -> Any`, `attack(Force, Asset) -> Any` | lowered | UnitGroupIssueOrder(attack, target group) | bound group target | order requested | damage/kill needs observed evidence | enemy -> Galaxy; ally -> intent |
| `block(Force, Region) -> Any` | lowered | UnitGroupIssueOrder(ForceField, center) | unit must actually have ForceField ability; region center | order requested | path denial needs observed check | enemy -> Galaxy; ally -> intent |
| `build(Force, Asset, Region) -> Any` | lowered | v04 scripted construction spawn | environment operation; not simulated worker control |  |  | enemy -> Galaxy; ally -> intent |
| `cancel(Asset) -> Any` | unsupported | none | no cancel lowerer |  |  | enemy -> unsupported; ally -> intent |
| `cast(Force, String) -> Any`, `cast(Force, String, Entity) -> Any`, `cast(Force, String, Region) -> Any` | lowered | UnitGroupIssueOrder(AbilityCommand(...)) | ability string and target shape require game-data validation | order requested | ability effect needs event/state check | enemy -> Galaxy; ally -> intent |
| `choose(String, String) -> Any` | lowered | v04 registry mapping: choose | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `clear_ability_cooldown(Entity, String, String) -> Any` | lowered | v04 registry mapping: clear_ability_cooldown | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `clear_cooldown(Entity, String) -> Any` | lowered | v04 registry mapping: clear_cooldown | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `clear_no_fly(Region) -> Any` | lowered | v04 registry mapping: clear_no_fly | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `clear_status_cooldown(Entity, String, String) -> Any` | lowered | v04 registry mapping: clear_status_cooldown | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `control(Force, Force) -> Any` | lowered | v04 scripted ownership rewrite | environment operation; not simulated worker control |  |  | enemy -> Galaxy; ally -> intent |
| `detach(Force, Number, Force) -> Any` | lowered | v04 registry mapping: detach | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_ability_charge_regen(Entity, String, String, Number, String) -> Any` | lowered | v04 registry mapping: force_ability_charge_regen | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_ability_cooldown(Entity, String, String, Number) -> Any` | lowered | v04 registry mapping: force_ability_cooldown | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_alliance(String, String, String) -> Any` | lowered | v04 registry mapping: force_alliance | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_charge_regen(Entity, String, Number, String) -> Any` | lowered | v04 registry mapping: force_charge_regen | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_cooldown(Entity, String, Number) -> Any` | lowered | v04 registry mapping: force_cooldown | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_disable(Entity, String) -> Any` | lowered | v04 registry mapping: force_disable | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_enable(Entity, String) -> Any` | lowered | v04 registry mapping: force_enable | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_face(Entity, Region) -> Any` | lowered | v04 registry mapping: force_face | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_hide(Entity, Bool) -> Any` | lowered | v04 registry mapping: force_hide | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_kill(Entity) -> Any` | lowered | v04 registry mapping: force_kill | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_owner(Entity, String) -> Any` | lowered | v04 registry mapping: force_owner | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_pause(Entity, Bool) -> Any` | lowered | v04 registry mapping: force_pause | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_remove(Entity) -> Any` | lowered | v04 registry mapping: force_remove | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_replace(Entity, String) -> Any` | lowered | v04 registry mapping: force_replace | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_sleep(Entity, Bool) -> Any` | lowered | v04 registry mapping: force_sleep | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_state(Entity, String, Bool) -> Any` | lowered | v04 registry mapping: force_state | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_status(Entity, String, String, Number) -> Any` | lowered | v04 registry mapping: force_status | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_status_charge_regen(Entity, String, String, Number, String) -> Any` | lowered | v04 registry mapping: force_status_charge_regen | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_status_cooldown(Entity, String, String, Number) -> Any` | lowered | v04 registry mapping: force_status_cooldown | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_status_duration(Entity, String, Number) -> Any` | lowered | v04 registry mapping: force_status_duration | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_status_off(Entity, String, String, Number) -> Any` | lowered | v04 registry mapping: force_status_off | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_status_remaining(Entity, String, Number) -> Any` | lowered | v04 registry mapping: force_status_remaining | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_status_stacks(Entity, String, Number) -> Any` | lowered | v04 registry mapping: force_status_stacks | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_teleport(Entity, Region) -> Any` | lowered | v04 registry mapping: force_teleport | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_upgrade(String, String, Number) -> Any` | lowered | v04 registry mapping: force_upgrade | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `force_vital(Entity, String, Number) -> Any` | lowered | v04 registry mapping: force_vital | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `forget(String) -> Any` | lowered | v04 registry mapping: forget | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `hold(Force) -> Any` | lowered | UnitGroupIssueOrder(stop) | bound force | stop order requested | no guaranteed sustained hold | enemy -> Galaxy; ally -> intent |
| `hold_window(Phase, Number) -> Any` | lowered | v04 registry mapping: hold_window | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `mark(String) -> Any` | lowered | v04 registry mapping: mark | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `move(Force, Region) -> Any`, `move(Force, Route) -> Any`, `move(Force, Location) -> Any` | lowered | UnitGroupIssueOrder(move, center) | target needs concrete point; Route is strategic only | order requested | arrival needs enter/count_in check | enemy -> Galaxy; ally -> intent |
| `no_fly(Region) -> Any` | lowered | v04 registry mapping: no_fly | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `pause_progress(Entity) -> Any` | lowered | v04 registry mapping: pause_progress | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `recenter(Region, Entity) -> Any` | lowered | v04 registry mapping: recenter | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `release(Force, Entity) -> Any` | lowered | v04 registry mapping: release | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `remember(String, Number) -> Any` | lowered | v04 registry mapping: remember | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `remember_event_unit(String, String) -> Any` | lowered | v04 registry mapping: remember_event_unit | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `remember_position(String, Entity) -> Any` | lowered | v04 registry mapping: remember_position | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `rescue(Entity, String) -> Any` | lowered | v04 registry mapping: rescue | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `reset_ability(Entity, String) -> Any` | lowered | v04 registry mapping: reset_ability | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `reset_cooldowns(Entity) -> Any` | lowered | v04 registry mapping: reset_cooldowns | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `restart_window(Phase, Number) -> Any` | lowered | v04 registry mapping: restart_window | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `restore_ability_charges(Entity, String, String) -> Any` | lowered | v04 registry mapping: restore_ability_charges | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `restore_charges(Entity, String) -> Any` | lowered | v04 registry mapping: restore_charges | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `restore_status_charges(Entity, String, String) -> Any` | lowered | v04 registry mapping: restore_status_charges | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `resume_window(Phase, Number) -> Any` | lowered | v04 registry mapping: resume_window | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `retarget(Force, Force) -> Any`, `retarget(Force, Asset) -> Any`, `retarget(Force, Entity) -> Any`, `retarget(Force, Region) -> Any` | lowered | UnitGroupIssueOrder(attack or move) | same-side target -> move to spawn point; opposing side -> attack | order requested | response and weakened defense need separate observation | enemy -> Galaxy; ally -> intent |
| `retreat(Force, Region) -> Any`, `retreat(Force, Route) -> Any`, `retreat(Force, Location) -> Any` | lowered | UnitGroupIssueOrder(move, center) | point target; Route is strategic only | move order requested | safe escape needs enter/count_in check | enemy -> Galaxy; ally -> intent |
| `reveal(String, Region, Number) -> Any` | lowered | v04 registry mapping: reveal | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `reveal_while(String, Region) -> Any` | lowered | v04 registry mapping: reveal_while | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `set_mode(Entity, String) -> Any` | lowered | UnitGroupIssueOrder(AbilityCommand(mode)) | mode must map to a real ability for unit type | order requested | mode state needs observation | enemy -> Galaxy; ally -> intent |
| `snapshot(String, Entity) -> Any` | lowered | v04 registry mapping: snapshot | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `spawn(Force, Region) -> Any`, `spawn(Force, Location) -> Any` | lowered | CreateUnits + add to stable group | spawn components and concrete target point | create requested | live unit count/position for effect | enemy -> Galaxy; ally -> intent |
| `spend_ability_charges(Entity, String, String, Number) -> Any` | lowered | v04 registry mapping: spend_ability_charges | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `spend_charges(Entity, String, Number) -> Any` | lowered | v04 registry mapping: spend_charges | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `spend_status_charges(Entity, String, String, Number) -> Any` | lowered | v04 registry mapping: spend_status_charges | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `strip_status(Entity, String) -> Any` | lowered | v04 registry mapping: strip_status | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `tag(Entity, String, Number) -> Any` | lowered | v04 registry mapping: tag | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `tally(String, Number) -> Any` | lowered | v04 registry mapping: tally | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `transfer(Force, Force) -> Any` | lowered | v04 registry mapping: transfer | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `transfer_status(Entity, Entity, String) -> Any` | lowered | v04 registry mapping: transfer_status | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |
| `transport(Force, Force, Region) -> Any`, `transport(Force, Force, Location) -> Any` | unsupported | none | no transport lowerer |  |  | enemy -> unsupported; ally -> intent |
| `unmark(String) -> Any` | lowered | v04 registry mapping: unmark | game-data links require engine validation |  | compiler mapping only; outcome requires observation | environment |

## Deliberately absent APIs

- `visible_count(observer, force)`: no observer-specific visibility semantics until fog, ownership, and visibility queries are modeled together.
- `can_reach(force, region)` is now implemented: at least one live member can reach the region center; this does not prove the whole group can traverse the entire region.
- `group_idle(force)` and `phase until idle(...)`: a per-unit idle event does not establish group completion, arrival, or success.
- `role`: a free-text strategic hint used for pattern diagnostics; it has no implicit Galaxy lowering.

