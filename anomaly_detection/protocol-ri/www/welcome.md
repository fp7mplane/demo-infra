# Welcome to the Mplane Supervisor Demonstration WEB UI!

This web interface (still under development) allows you to control an Mplane Supervisor and access measurement results from the attached Probes and Repositories.

Please report problems and suggestions to the developer team, i.e. [tufa@netvisor.hu](mailto:
tufa@netvisor.hu)

###Instructions for use.

1. To start a measurement on a probe, go to the **Capabilities** tab, select one of the offered capabilities (check a cap., click **Create specification** and fill the non-fixed parameters required. (*Make sure to enter syntactically correct values, otherwise you may crash the supervisor*).

2. The specification will be in a **Pending** state for a while, you can check it on the next tab.

3. If you do no longer see your spec pending, it may have finished, and available on the **Results** tab. If you click the magnifier lens line, you see a dialog box with the returned values, and if the result is a time series, you can also see your data on a chart.

4. It is also possible to display multiple results (time-based results only) on a single page, i.e. on the **On-Demand Chart View**. To add a chart on here, open the third tab within the results dialog and select one of the 8 fields, that represent the chart spaces on the on-demand view.

### Page tree
- **Components**
 - **Capabilities** - all the registered capablities are listed here. Specifications can be generated after selecting the right specification. In the pop-up window the parameter constraints are pre-filled, these must be modified.
 - **Pending measurements** - the spicification having no results and receipts are displayed here
 - **Results** - the collected results can be viewd and visualized via this tab. A user-dependent visualization is avaible by dropping the the parameter to the selected chart-box via the "Add to pn-demand" tab.
 - **On-Demand Charts** - view the previously configured chart composition
- Dashboard
- Settings - user credentials can be managed here

###Limitations

...maybe too many to fully enumerate....

- The On-Demand Chart view will allow you to set the display period for your charts (currently does not).
- It will also be possible, to see multiple instances of the same measurement (i.e. same probe, same parameters, except for time) "concatenated" into a single chart line.
- Multi-line charts, and further chart customizations are also planned.
- **Dashboard** and **Settings** tabs are just dummies for now.
- If you reload the browser, your On-demand view (and other settings) are cleared.

