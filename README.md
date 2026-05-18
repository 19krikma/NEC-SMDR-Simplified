<h1>NEC SMDR (SIMPLIFIED)</h1>

<h2>About It</h2>
<p><b>NEC SMDR (SIMPLIFIED)</b> is same as <b>"NEC SMDR Logger"</b> but database removed, notifications removed, scripts to run continuously removed and script redesigned
to run certain duration instead of running continuously retrieving SMDR data. This script has all configuration moved to <b>config.yaml</b>. The script is flexible in terms
 of how many servers it can track at once, I haven't tested the limits so feel free to explore that limit, I suspect the limit of how many servers it can track at once
 will come down to your computers hardware capabilities.</p>

<h2>Disclaimer</h2>
<p>Script was formatted by AI. Exception handling was improved by AI but was checked and approved by me.</p>

<h2>SV9100 Setup</h2>
<ul>
  <li>Login into SV9100</li>
  <li>Click - System Data</li>
  <li>Click - 10-XX: System Confirguration</li>
  <li>Click - 10-20 : External Equipment LAN Setup</li>
  <li>Type Port Number of your Choice into -> 05 - SMDR Output</li>
  <img width="361" height="545" alt="Capture" src="https://github.com/user-attachments/assets/a6f3d35d-9a42-4de2-ba2c-33181d57d9bc" />
  <li>Click - Apply</li>
  <li>Scroll Down and Click - 35-XX: SMDR and Account Codes</li>
  <li>Click - 35-01 : SMDR Options</li>
  <li>Set -> 01 - Output Port Type = LAN</li>
  <img width="311" height="331" alt="Capture" src="https://github.com/user-attachments/assets/a9953d4c-3c8b-49a2-84bc-11e652d82d61" />
  <li>Click - Apply</li>
  <li>Click - 35-02 : SMDR Output Options</li>
  <li>Setup sameway like the screenshott below</li>
  <img width="422" height="486" alt="Capture" src="https://github.com/user-attachments/assets/c54d5e58-7314-4027-bc58-89d0bdb15c92" />
  <li>Click - Apply</li>
  <li>Click - Home</li>
  <li>Click - Logout</li>
</ul>
