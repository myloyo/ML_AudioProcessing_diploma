
namespace AudioProcessing.Domain.Entities.Track;

public class CreateTrackRequest
{
    public string Filename { get; set; } = null!;
    public string StorageKey { get; set; } = null!;
}