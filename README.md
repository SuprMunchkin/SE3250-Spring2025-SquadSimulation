This code simulates a small squad of troops patroling for hostiles in a defined area.

The model can be run by opening up the the jupyter noebook in a suitable environment. At this time, we have only tested it in Google Colab, but it should be albe to work in any jupyter environment that can execute the git clone command in the top block of the notebook. All blocks should be invoked in order.

Alternatively, you can compile the code into a docker container using the provided docker file and run app.py, a flask server which will serve up the simulation as a simple web page. This functionality has only been tested inside of github codespaces, but in theory it should work in other container environments, provided the networking is configured correctly to allow you to access the page. *Note: Batch run functionality is not yet working on the web interface.

Regardless of how you invoke the code, you should see a very simple user interface. Stock refers to the starting number of troops. Direction deviation is how far the blue squad is allowed to turn in each time step of the simulation. Playing around with the single run simulation should give you a feel for how the friendly squad behaves as you vary this parameter.
