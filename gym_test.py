import helics as h

def create_federate(step_size=1.0, offset=0.0):
    fedinfo = h.helicsCreateFederateInfo()

    h.helicsFederateInfoSetCoreName(fedinfo, "SimpleFederate")
    h.helicsFederateInfoSetCoreTypeFromString(fedinfo, "zmq")
    h.helicsFederateInfoSetCoreInitString(fedinfo, "--federates=1")

    h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_delta, step_size)
    h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_period, step_size)

    # Create value federate
    vfed = h.helicsCreateValueFederate("SimpleFederate", fedinfo)
    print("Created federate")

    # Register publication and subscription (double type)
    pub = h.helicsFederateRegisterGlobalPublication(vfed, "vent_q", h.HELICS_DATA_TYPE_DOUBLE, "Wh")
    sub = h.helicsFederateRegisterSubscription(vfed, "Envelope/0/zone.ac_t 8674", "")
    sub2 = h.helicsFederateRegisterSubscription(vfed, "Weather/0/drybulb", "")

    h.helicsFederateEnterInitializingMode(vfed)
    h.helicsFederateEnterExecutingMode(vfed)
    print("Entered execution mode")

    current_time = offset
    while current_time < 10.0:
        current_time = h.helicsFederateRequestTime(vfed, current_time)
        print(f"\n[Time {current_time:.2f}]")

        if h.helicsInputIsUpdated(sub):
            value = h.helicsInputGetDouble(sub)
            print(f"Received: {value:.3f}")
        else:
            value = 0.0
            print("No new input. Using default:", value)

        output_value = value + 1.0
        h.helicsPublicationPublishDouble(pub, output_value)
        print(f"Published: {output_value:.3f}")

    # Finalize
    h.helicsFederateFinalize(vfed)
    h.helicsFederateFree(vfed)
    h.helicsCloseLibrary()
    print("Federate finalized")

if __name__ == "__main__":

    step= 3600
    offset=0

    create_federate(step_size=step, offset=offset)
