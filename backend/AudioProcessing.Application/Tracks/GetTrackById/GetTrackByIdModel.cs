
namespace AudioProcessing.Application.Tracks.GetTrackById;

public record GetTrackByIdModel(
    Guid TrackId,
    string InputKey,
    string OutputKey,
    string Filename,
    DateTime CreatedAt,
    DateTime? DeletedAt
);
