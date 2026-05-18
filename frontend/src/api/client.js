import axios from "axios";

const api = axios.create({ baseURL: "/api" });

export const fetchTeams   = ()                        => api.get("/teams").then(r => r.data);
export const fetchVenues  = ()                        => api.get("/venues").then(r => r.data);
export const fetchH2H     = (t1, t2)                 => api.get(`/h2h/${t1}/${t2}`).then(r => r.data);
export const fetchTeamStats = (team)                 => api.get(`/team-stats/${team}`).then(r => r.data);
export const fetchVenueStats = (venue)               => api.get(`/venue-stats/${encodeURIComponent(venue)}`).then(r => r.data);
export const fetchModelMetrics = ()                  => api.get("/model-metrics").then(r => r.data);
export const fetchRecentMatches = (n = 15)           => api.get(`/recent-matches?n=${n}`).then(r => r.data);
export const postPredict  = (payload)                => api.post("/predict", payload).then(r => r.data);
