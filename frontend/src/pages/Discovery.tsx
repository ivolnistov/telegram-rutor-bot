import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  addToWatchlist,
  createSearch,
  deleteRating,
  downloadTorrent,
  getMe,
  getMediaAccountStates,
  getMediaTorrents,
  getPersonalRecommendations,
  getRatedMedia,
  getRecommendations,
  getTrending,
  rateMedia,
  searchDiscovery,
  syncLibrary,
} from "api";
import { Button } from "components/ui/Button";
import { Modal } from "components/ui/Modal";
import { useDebounce } from "hooks/useDebounce";
import {
  Check,
  Eye,
  Loader2,
  RefreshCw,
  Rss,
  Search,
  Star,
} from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import type { TmdbMedia } from "types";

const MediaModal = ({
  media,
  onClose,
}: {
  media: TmdbMedia;
  onClose: () => void;
}) => {
  const { t } = useTranslation();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const queryClient = useQueryClient();

  const { data: user } = useQuery({
    queryKey: ["me"],
    queryFn: getMe,
    staleTime: Infinity,
  });

  const handleSubscribe = async () => {
    if (!user) {
      toast.error(t("error"));
      return;
    }

    setIsSubmitting(true);
    try {
      let title =
        media.title ||
        media.name ||
        media.original_title ||
        media.original_name ||
        "";

      const releaseDate = media.release_date || media.first_air_date;
      if (releaseDate) {
        const year = releaseDate.split("-")[0];
        if (year) {
          title += ` ${year}`;
        }
      }

      const url = `https://rutor.info/search/0/0/0/0/${encodeURIComponent(title || "")}`;
      const cron = "0 */4 * * *"; // Every 4 hours

      const formData = new FormData();
      formData.append("url", url);
      formData.append("cron", cron);
      formData.append("category", "Films");
      formData.append("chat_id", String(user.chat_id));

      await createSearch(formData);
      toast.success(t("discovery.subscribed") || "Subscribed successfully");
    } catch {
      toast.error(t("error"));
    } finally {
      setIsSubmitting(false);
    }
  };

  const { data: recommendations } = useQuery({
    queryKey: ["recommendations", media.id],
    queryFn: () => getRecommendations(media.title ? "movie" : "tv", media.id),
    enabled: !!media.id,
  });

  const { data: accountStates } = useQuery({
    queryKey: ["accountStates", media.id],
    queryFn: () =>
      getMediaAccountStates(media.title ? "movie" : "tv", media.id),
    enabled: !!media.id,
  });

  const { data: linkedTorrents } = useQuery({
    queryKey: ["mediaTorrents", media.title ? "movie" : "tv", media.id],
    queryFn: () => getMediaTorrents(media.title ? "movie" : "tv", media.id),
    enabled: !!media.id,
  });
  const userRating =
    accountStates?.rated && typeof accountStates.rated !== "boolean"
      ? accountStates.rated.value
      : 0;

  const inLibrary = accountStates?.in_library;
  const inWatchlist = accountStates?.watchlist;

  const handleWatchlist = async () => {
    try {
      await addToWatchlist(
        media.title ? "movie" : "tv",
        media.id,
        !inWatchlist,
      );
      toast.success(
        inWatchlist ? "Removed from Watchlist" : "Added to Watchlist",
      );
      await queryClient.invalidateQueries({
        queryKey: ["accountStates", media.id],
      });
      // Invalidate discovery to update watchlist feed if implemented/visible
    } catch {
      toast.error(t("error"));
    }
  };

  const handleRate = async (value: number) => {
    try {
      if (value === userRating) {
        await deleteRating(media.title ? "movie" : "tv", media.id);
        toast.success(t("discovery.rating_removed") || "Rating removed");
      } else {
        await rateMedia(media.title ? "movie" : "tv", media.id, value);
        toast.success(t("discovery.rated") || "Rated successfully");
      }
      await queryClient.invalidateQueries({
        queryKey: ["accountStates", media.id],
      });
      await queryClient.invalidateQueries({ queryKey: ["discovery", "rated"] });
    } catch {
      toast.error(t("error"));
    }
  };

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={media.title || media.name || "Unknown"}
    >
      <div className="space-y-6">
        <div className="aspect-video w-full rounded-lg overflow-hidden bg-black/20 relative">
          <img
            src={`https://image.tmdb.org/t/p/w780${media.backdrop_path || media.poster_path || ""}`}
            alt={media.title || media.name}
            className="size-full  object-cover"
          />
          <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/90 to-transparent">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-amber-400">
                <Star className="size-4 fill-amber-400" />
                <span className="font-bold">
                  {media.vote_average.toFixed(1)}
                </span>
              </div>
              {inLibrary && (
                <div className="flex items-center gap-1 bg-green-500/20 text-green-400 px-2 py-0.5 rounded text-xs font-medium border border-green-500/20">
                  <Check className="size-3" />
                  In Library
                </div>
              )}
            </div>
          </div>
        </div>

        <p className="text-zinc-300 text-sm leading-relaxed">
          {media.overview || t("discovery.no_overview")}
        </p>

        {/* Rating Section */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-zinc-400">
            {t("discovery.your_rating")}
          </h4>
          <div className="flex gap-1">
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((star) => (
              <button
                key={star}
                onClick={() => {
                  void handleRate(star);
                }}
                className="group focus:outline-none"
              >
                <Star
                  className={`size-5 transition-colors ${
                    userRating >= star
                      ? "fill-amber-400 text-amber-400"
                      : "text-zinc-700 hover:text-amber-400 hover:fill-amber-400"
                  }`}
                />
              </button>
            ))}
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-zinc-800">
          <Button variant="ghost" onClick={onClose}>
            {t("common.close")}
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              void handleWatchlist();
            }}
          >
            {inWatchlist ? (
              <>
                <Check className="size-4 mr-2" />
                In Watchlist
              </>
            ) : (
              <>
                <Eye className="size-4 mr-2" />
                Add to Watchlist
              </>
            )}
          </Button>
          <Button
            onClick={() => {
              void handleSubscribe();
            }}
            disabled={isSubmitting || !user}
          >
            {isSubmitting ? (
              <Loader2 className="size-4 mr-2 animate-spin" />
            ) : (
              <Rss className="size-4 mr-2" />
            )}
            {t("discovery.subscribe") || "Subscribe"}
          </Button>
        </div>

        {/* Recommendations */}
        {recommendations && recommendations.length > 0 && (
          <div className="space-y-3 pt-4 border-t border-zinc-800">
            <h4 className="text-sm font-medium text-zinc-400">
              {t("discovery.recommendations")}
            </h4>
            <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
              {recommendations.slice(0, 4).map((rec) => (
                <div
                  key={rec.id}
                  className="aspect-[2/3] bg-zinc-800 rounded overflow-hidden relative group cursor-pointer"
                  title={rec.title || rec.name}
                  onClick={() => {
                    // Logic to switch modal content would be needed here,
                    // but for now simplistic approach (recursive modal or replace state)
                    // Ideally we just close and open new one, but onClose is passed from parent.
                    // Let's just ignore click or implement proper nav.
                  }}
                >
                  <img
                    src={`https://image.tmdb.org/t/p/w300${rec.poster_path || ""}`}
                    alt={rec.title || rec.name}
                    className="size-full  object-cover opacity-80 group-hover:opacity-100 transition-opacity"
                  />
                  {(rec as unknown as { in_library: boolean }).in_library && (
                    <div className="absolute top-1 right-1 bg-green-500/90 text-white p-0.5 rounded-full shadow-sm">
                      <Check className="size-2.5" />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Linked Torrents */}
        {linkedTorrents && linkedTorrents.length > 0 && (
          <div className="space-y-3 pt-4 border-t border-zinc-800">
            <h4 className="text-sm font-medium text-zinc-400">
              Linked Torrents
            </h4>
            <div className="space-y-2">
              {linkedTorrents.map((torrent) => (
                <div
                  key={torrent.id}
                  className="flex items-center justify-between p-2 rounded bg-zinc-800/50 border border-zinc-700/50"
                >
                  <div className="flex-1 min-w-0 mr-4">
                    <div
                      className="text-sm font-medium text-zinc-200 truncate"
                      title={torrent.name}
                    >
                      {torrent.name}
                    </div>
                    <div className="text-xs text-zinc-500 mt-0.5">
                      {(torrent.sz / 1024 / 1024 / 1024).toFixed(2)} GB •{" "}
                      {new Date(torrent.created).toLocaleDateString()}
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="secondary"
                    className="h-7 text-xs"
                    onClick={() => {
                      void (async () => {
                        try {
                          await downloadTorrent(torrent.id);
                          toast.success(t("library.download_started"));
                        } catch {
                          toast.error(t("library.download_failed"));
                        }
                      })();
                    }}
                  >
                    <Check className="size-3 mr-1.5" />
                    Download
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
};

// Start of DiscoveryPage

const DiscoveryPage = () => {
  const { t } = useTranslation();
  const [searchQuery, setSearchQuery] = useState("");
  const debouncedQuery = useDebounce(searchQuery, 500);

  const [contentType, setContentType] = useState<"movie" | "tv">("movie");
  const [feedType, setFeedType] = useState<"trending" | "personal" | "rated">(
    "trending",
  );

  const [selectedMedia, setSelectedMedia] = useState<TmdbMedia | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);

  const { data: displayData, isLoading } = useQuery({
    queryKey: ["discovery", feedType, contentType, debouncedQuery],
    queryFn: () => {
      if (debouncedQuery) return searchDiscovery(debouncedQuery);
      if (feedType === "personal") return getPersonalRecommendations(); // Note: check backend impl
      if (feedType === "rated") return getRatedMedia(contentType);
      return getTrending(contentType);
    },
  });

  const handleSync = async () => {
    setIsSyncing(true);
    try {
      const { matched } = await syncLibrary();
      toast.success(`Library synced. Matched ${String(matched)} films.`);
      // Invalidate queries to refresh "in_library" badges
      // queryClient.invalidateQueries({ queryKey: ["discovery"] }); // need queryClient
    } catch {
      toast.error("Failed to sync library");
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div>
      <div className="flex flex-col xl:flex-row items-start xl:items-center justify-between gap-4 mb-8">
        <div className="flex flex-col md:flex-row items-stretch md:items-center gap-4 w-full">
          {/* Feed Type Toggles */}
          <div className="flex bg-zinc-900 border border-zinc-800 rounded-lg p-1 self-start md:self-auto">
            <button
              onClick={() => {
                setFeedType("trending");
              }}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
                feedType === "trending"
                  ? "bg-zinc-800 text-white shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              Trending
            </button>

            <button
              onClick={() => {
                setFeedType("rated");
              }}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
                feedType === "rated"
                  ? "bg-amber-600 text-white shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              Rated
            </button>

            <button
              onClick={() => {
                setFeedType("personal");
              }}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
                feedType === "personal"
                  ? "bg-violet-600 text-white shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              For You
            </button>
          </div>
          {/* Content Type Toggles */}
          <div
            className={`flex bg-zinc-900 border border-zinc-800 rounded-lg p-1 transition-opacity self-start md:self-auto ${
              feedType === "personal"
                ? "invisible opacity-0"
                : "visible opacity-100"
            }`}
            aria-hidden={feedType === "personal"}
          >
            <button
              onClick={() => {
                setContentType("movie");
              }}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
                contentType === "movie"
                  ? "bg-zinc-800 text-white shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
              tabIndex={feedType === "personal" ? -1 : 0}
            >
              {t("discovery.movies")}
            </button>
            <button
              onClick={() => {
                setContentType("tv");
              }}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
                contentType === "tv"
                  ? "bg-zinc-800 text-white shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
              tabIndex={feedType === "personal" ? -1 : 0}
            >
              {t("discovery.tv_shows")}
            </button>
          </div>
          <div className="flex-1" /> {/* Spacer */}
          <div className="flex items-center gap-2 w-full md:w-auto">
            <div className="relative w-full md:w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-zinc-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                }}
                placeholder={t("discovery.search_placeholder")}
                className="w-full bg-zinc-900 border border-zinc-800 text-zinc-200 rounded-lg pl-9 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/50"
              />
            </div>
            <Button
              variant="outline"
              size="icon"
              onClick={() => {
                void handleSync();
              }}
              disabled={isSyncing}
              title="Sync Library"
            >
              {isSyncing ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <RefreshCw className="size-4" />
              )}
            </Button>{" "}
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="size-8 animate-spin text-zinc-500" />
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {displayData?.map((media) => (
            <div
              key={media.id}
              className="group relative aspect-[2/3] bg-zinc-900 rounded-lg overflow-hidden border border-zinc-800 hover:border-violet-500/50 transition-all cursor-pointer"
              onClick={() => {
                setSelectedMedia(media);
              }}
            >
              {media.poster_path ? (
                <img
                  src={`https://image.tmdb.org/t/p/w500${media.poster_path}`}
                  alt={media.title || media.name}
                  className="size-full  object-cover transition-transform duration-500 group-hover:scale-110"
                />
              ) : (
                <div className="size-full  flex items-center justify-center text-zinc-700">
                  ?
                </div>
              )}

              {(media as unknown as { in_library: boolean }).in_library && (
                <div className="absolute top-2 right-2 z-10 bg-green-500 text-white p-1 rounded-full shadow-md">
                  <Check className="size-3" />
                </div>
              )}

              <div className="absolute inset-x-0 bottom-0 p-3 bg-gradient-to-t from-black/90 via-black/60 to-transparent pt-12 opacity-0 group-hover:opacity-100 transition-opacity">
                <h4 className="text-sm font-medium text-white line-clamp-2">
                  {media.title || media.name}
                </h4>
                <div className="flex items-center gap-2 mt-1">
                  <Star className="size-3 fill-amber-400 text-amber-400" />
                  <span className="text-xs text-zinc-300">
                    {media.vote_average.toFixed(1)}
                  </span>
                  <span className="text-xs text-zinc-500">•</span>
                  <span className="text-xs text-zinc-400">
                    {(media.release_date || media.first_air_date)?.split(
                      "-",
                    )[0] || "?"}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedMedia && (
        <MediaModal
          media={selectedMedia}
          onClose={() => {
            setSelectedMedia(null);
          }}
        />
      )}
    </div>
  );
};
export default DiscoveryPage;
