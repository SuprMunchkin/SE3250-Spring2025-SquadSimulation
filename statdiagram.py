%%plantuml
@startuml
title GoodUnit State Diagram

[*] --> Spawning : created

state Spawning {
  [*] --> Placing
  Placing --> Moving : _start_at_random_edge()
}

Moving --> Battling : encounter BadUnit
Battling --> Moving : survives battle
Battling --> Dead : num_people <= 0

Moving --> Retreating : energy <= 0 and exiting = True
Retreating --> Exited : reaches edge
Retreating --> Battling : encounter BadUnit

@enduml
