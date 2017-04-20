------------------- Generate road network -----------------
Edit ./conf.txt file.

Run in terminal:

./1gennode.py
./2genedge.py
./3genconnect.py
./4netconvert.py


----------------- Generate random vehicle routes ----------
./5genroutes.py 
./6gensumocfg.py


----------------- SUMO ---------------
net.cnd.tls.net.xml is the final input to the SUMO simulation.


----------------- Python -------------
Main python file connecting to SUMO simulator via Traci: 
python ./runner.py

Modules for cars: sumo_car.py
Modules for traffic signals: sumo_tls.py