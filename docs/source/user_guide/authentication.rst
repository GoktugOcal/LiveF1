.. _authentication:

Authentication
==============

Formula 1 live timing data requires an F1 account with an active **F1TV
subscription**. LiveF1 signs in with your account email and password and sends
the resulting subscription token with every request to
``livetiming.formula1.com``, both for historical (static) data and for the
real-time client.

Signing in
----------

.. code-block:: python

    import livef1

    livef1.login()

``login()`` looks for credentials in this order:

1. The ``username`` and ``password`` arguments.
2. The ``F1_USERNAME`` and ``F1_PASSWORD`` environment variables.
3. The same variables in a ``.env`` file (``.env`` in the current directory by default):

   .. code-block:: bash

       F1_USERNAME='you@example.com'
       F1_PASSWORD='your-password'

4. An interactive prompt. After a successful sign-in, the entered values are
   saved to the ``.env`` file, readable by your user only. Keep this file out
   of version control.

If no credentials are available and the session is not interactive, an
``AuthenticationError`` is raised.

You do not have to call ``login()`` yourself: when live timing rejects a
request, LiveF1 signs in once and retries it.

Reusing the token
-----------------

The token is saved to ``~/.livef1/token.json`` and reused until it expires, so
you are not signed in again on every run.

.. code-block:: python

    # Sign in again even if a valid token is saved
    livef1.login(force=True)

    # Keep the token in memory only
    livef1.login(save_token=False)

    # Save the token somewhere else
    livef1.login(token_path="/path/to/token.json")

    # Read and save credentials in another .env file
    livef1.login(env_path="/path/to/.env")

    # Delete the saved token (the .env file is kept)
    livef1.logout()

To set these options once for all sign-ins, including the automatic ones, use
:func:`livef1.configure`:

.. code-block:: python

    livef1.configure(
        auth_save_token=True,
        auth_token_path="/path/to/token.json",
        auth_env_path="/path/to/.env",
    )

Overriding the sign-in configuration
------------------------------------

The OAuth client ID and policy ID are read from the F1 account website. If F1
changes the website before LiveF1 is updated, set ``LIVEF1_F1_CLIENT_ID`` and
``LIVEF1_F1_POLICY_ID`` to override them.
