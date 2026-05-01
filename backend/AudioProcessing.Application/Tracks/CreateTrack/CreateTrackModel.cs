namespace AudioProcessing.Application.Tracks.CreateTrack;

public record CreateTrackModel(Guid TrackId, string Filename, string InputKey, string OutputKey, DateTime CreatedAt);
