export {
  listGames,
  getGame,
  getTurnStatus,
  createGame,
  getGalaxy,
  getPlayerState,
  previewRace,
  getRace,
  getPredefinedRaces,
  submitCommands,
  getCommands,
  postAuthSession,
  setAuthTokenGetter,
  ApiError,
  AuthError,
} from "./client";

export type {
  GameSummary,
  GameDetail,
  TurnStatus,
  PlayerSubmissionInfo,
  CreateGameResponse,
  SubmitCommandsResponse,
  AuthSessionResponse,
  AuthTokenGetter,
  CommandsResponse,
} from "./client";
