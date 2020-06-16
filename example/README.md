# DRF Integrations Framework Example - e-commerce analytics platform

This Django app is an example of a hypothetical e-commerce analytics platform. This system serves multiple clients
(`Organisation`s), that have multiple customers (`User`s) purchasing in many different e-commerce platforms, and want
to see the purchase events in many different analytics tools. There are 3 different integrations here:

- The communication of the organisations with the system. They can create users in this system through its users API,
which uses OAuth2 for authentication and authorization.
- The communication of the e-commerce platforms with the system. They will send purchase events through the
integrations API.
- The communication of the system with the analytics tools. Each time the system processes a purchase event, it will
send it to the different analytic instances of the organisation where the user doing the purchase belongs.

![Diagram](http://www.plantuml.com/plantuml/png/SoWkIImgAStDuKhEoIzDKQZcKb283ix8ByXCgupbgkNYoijFIGMBQcWgA7c4X0GeAIGMAtWQOeWOWtLM5fUave8qGit3r6a4KkURML6Gc9UQ0rO9jqz1joWpFQD4rmvalgSXZ8im5if0A0GPvsa4uoARY-G0c7w5v9pCrBoIOh2b2ADIyilpT47kzpHMi87mC7KufEQb04C90000)

In this example 3 different integrations have been implemented:
- A Shopify integration. It includes a `BaseIntegration` implementation with a configuration form, an authentication
backend, permission model and a viewset.
- A Mixpanel integration. It includes a `BaseIntegration` implementation with a configuration form and a client.
- An API integration. It simply includes a `BaseIntegration` implementation.

The organisations can create users through the API and associate their IDs to the IDs in each of the e-commerce
platforms. Then, the system will ingest purchase events from e-commerce platforms. As each event comes from a specific
installation, the purchase can be stored against it. Finally, each time a new purchase is processed, an event is
gonna be sent to each registered analytics tool in the organisation.

Using DRF Integrations Framework the work has been simplified, as:

- Each organisation can install as many integrations as there are available. In this example it is only Shopify and
Mixpanel, but adding BigCommerce, WooCommerce, Braze, etc. is really simple, just create a new integration and it will
be immediately available for clients to install.
- The logic between ingesting events and sending them to the analytics tools is split. Adding new e-commerce platforms
does not have any impact on how the rest of the system behaves. Furthermore, adding a new integration automatically
takes advantage of the rest of the logic already built in the system.
