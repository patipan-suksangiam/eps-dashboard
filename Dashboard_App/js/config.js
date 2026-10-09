// ⚙️ EPS Dashboard — deployment config
//
// Leave EPS_DATA_BASE EMPTY ('') to load RAW_Data from the same origin
// (local web server, Synology, or GitHub Pages with RAW_Data committed).
//
// Point it at an external host to keep the real customer data OUT of this repo.
// The host MUST send CORS headers (Access-Control-Allow-Origin) for the CSVs.
// Example:
//   window.EPS_DATA_BASE = 'https://data.example.com/RAW_Data/';
//
window.EPS_DATA_BASE = '';
