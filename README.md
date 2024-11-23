# TE3003B
La organizacion del repo va separada la seccion de reto de las actividades y los minichallenges.Cada vez que hagan un `git pull` muevanse a la carpeta principal de `catkin_ws` y hagan un `catkin_make` para actualizar los paquetes 

Comandos utiles github 
```
git commit -m "Mensaje del commit"
git add --all #En caso de que te marque error en el commit
git push #Cargar a la branch actual
git pull #Actualizar repositorio local con la branch actual
```

Dependencias recomentdadas de paquete  
```# Autonomous Navigation 

## Project description

The goal of this project was to develop scripts and tools too ensure the positioning of a Manchester Puzzlebot throught a maze

## Topics:

- Autonomous Robots: Navigation stack 
- Embedded Systems: Kalman Filters
- Integration: Modbus, ULite, 
- Positioning: Arucos, LiDAR

## Project Solutions

The project was a mobile robot capable of reaching points in a cartesian plane aboiding obstacles (Navigation stack was prohibited for the challenge). 

- Positioning: Differential drive estimation, Kalman Filter (using arucos as a reference)
- Obstacle handling: Avoid obstacle algorithm using LiDAR 
- Route Planning: Bug 0 & Bug 2 algorithms, (Additional LiDAR clearshot)

<img src="./images/20240605_172201.jpg" alt="Gripper" width="250"/>
<img src="./images/IMG-20240605-WA0123.jpg" alt="Gripper" width="250"/>

## Cobots - Extra

In order to compete in "Expo Ingenierias" that year we added the functions to calaborate with ULite cobots for a pick and place

- Communications: TCP/IP using ROS 
- Cargo Placement: Using arucos to correct and relate the place

<img src="./images/ULite_cob.jpg" alt="Gripper" width="250"/>

## Recicled Materials - Extra

During the course we manufactured the maze using reciled materials, the most challenging ones were PP (polypropylene) and PLA (polylactic acid). 

<img src="./images/Pista_1.jpg" alt="Gripper" width="250"/>
<img src="./images/Pista_2.jpg" alt="Gripper" width="250"/>
<img src="./images/Pista_3.jpg" alt="Gripper" height="200"/>
<img src="./images/Pista_4.jpg" alt="Gripper" height="200"/>
catkin_create_pkg minichalN rospy roscpp tf geometry std_msgs
```

Informacion adicional se puede encontrar en el repo de manchester:
> https://github.com/ManchesterRoboticsLtd/TE3003B_Integration_of_Robotics_and_Intelligent_Systems/tree/main/Week%202

Y los trabajos no relacionados con programacion en el drive 
> https://drive.google.com/drive/folders/1jOVFzzcgHFuTUMrlBhWRhG6dwu3PBKUQ?usp=sharing


