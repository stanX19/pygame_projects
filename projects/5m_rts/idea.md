Game: 5m war

RTS games are fun but often takes a lot of time. Hereby I propose a RTS game that ends in 5 minutes

note: a tile is (0, 0) to (1, 1) in cartesian coordinate

Map: cartesian map with different points that lies on any spot (should be completely observable without dragging)
- Castle: tile based. each player or bot's base, it is the primary objective of the game. losing it ends the game for that player
- Resource points: tile based. capturing it generates resources overtime. resources are used to spawn units and upgrading buildings
- Rivers & mountains: tile based. serves as obstacles for armies. cannot have constructions. should have appropriate pathfinding algo

Battle:
- collision results in a fight, both units will stop until one dies, if 3 or more collide, all of them will stop and fight
- units cannot overlap, they push each other apart
- Fighting mechanism is a simple attack + cd + hp combination, real time and should end fast.
- Units will automatically find closest enemy in certain radius to attack if exist
- Strategic points such as castle and rouge resource points have a certain hp, requires killing it to capture
- when two unit enter the same strategic point, the rouge resource point will attack randomly

Upgrade: enhancing units and building using points
- resource points: increase resource output speed
- castle: increase hp / atk / -cd seperately
- unit: increase hp / atk / cd / movement speed separately
- castle to castle movement speed: by default its 3x normal speed (thats why its strategic), but it can be upgraded permanently between all castles

Controls: how the player and bot play
- unit spawn: tap on tower to spawn 1 unit near the castle using 1 resource point
- select unit: tap on a unit or selecting a range of units (swipe) sets them as selected
- send out armies: dragging selected untis from one point to another. this commands all selected unit in to move towards that specific point.
- upgrading unit: side panel ui to upgrade specific traits of units / castle / resource points
- building castle: holding >10 selected allied units (with finger) builds a castle and deducts 10 resource points

Mechanics:
- each player starts with 10 unit
- resource buildup: resource point generate resource x times faster at the x minute of the game 
- sudden death: at 4:00 mark all resource point are destroyed, and a lot of resource points are refunded for that. movement speed x3, players have to fight with what they have

UI design:
- units: colored squares, triangle, circles
- other elements: sprite

Win condition: destroy all castle of enemies on the map
Lose condition: lose all castle

MVP idea testing: Pygame, single player PVE
System architecture: ECS, Spatial Hashing based collision check optimization (only check within chunk and neighbour tiles)

