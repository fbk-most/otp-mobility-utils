# OpenTripPlanner - Application to the case of Bologna
With the final goal of comparing the travel times between zones with different mode of transport, this repository has the goal to implement a structured setting for extracting travel times through OpenTripPlanner (OTP).

OTP should be installed in the same folder of the repository. `otp-shaded-2.7.0.jar` should hence be downloaded from [this page](https://repo1.maven.org/maven2/org/opentripplanner/otp-shaded/2.7.0/) and then located in the OpenTripPlanner main folder. 

OTP should also be active when asking queryes to it. Locate in the folder of the project, then run this command from terminal: `java -Xmx2G -jar otp-shaded-2.7.0.jar --build --serve`.

Some OTP default values were changed for this configuration. This changes are explicited in the file `router-config.json`.

The core code, which inspects the possible travel solutions and return the travel times between zones, is `otp-processor.py`. The query starts by calling `python otp_processor.py XXX`, where `XXX` is argument `"CAR"` or `"TRANSIT"` for specifying the transport mode.

For this code to work, the input data are:
- *data representing the infrastructure and service*. They should be present in the main folder of the repository
    - a pbf file with the OpenStreetMap *roads*. It has been created following the instructions described in the [OTP Basic Tutorial](https://docs.opentripplanner.org/en/latest/Basic-Tutorial/), that is, starting from the pbs of the Europe then using [Osmium tools](https://osmcode.org/osmium-tool/) to limit it with a buffer and a query for highways.
    - a zip file with the GTFS of the public transportation *schedule*. Downloaded from [here](https://solweb.tper.it/web/tools/open-data/open-data.aspx).
- *data representing the starting and ending points of the trips*, of which the travel time is to be assessed. They sould be located in the folder data/input_od.
The output travel times will be saved in the folder data/output.