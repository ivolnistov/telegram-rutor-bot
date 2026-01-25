import { useQuery } from "@tanstack/react-query";
import { downloadTorrent, getTorrents } from "api";
import { Button } from "components/ui/Button";
import { Input } from "components/ui/Input";
import { useDebounce } from "hooks/useDebounce";
import { Download, Search } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import type { Torrent } from "types";

const LibraryPage = () => {
  const { t } = useTranslation();
  const [searchQuery, setSearchQuery] = useState("");
  const debouncedQuery = useDebounce(searchQuery, 300);

  const { data: torrents, isLoading } = useQuery({
    queryKey: ["torrents", debouncedQuery],
    queryFn: () => getTorrents(100, debouncedQuery),
  });

  return (
    <div>
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 mb-8">
        <h3 className="text-xl font-semibold">{t("library.title")}</h3>
        <div className="w-full md:w-64">
          <Input
            icon={<Search className="size-4 " />}
            type="text"
            placeholder={t("library.search_placeholder")}
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
            }}
          />
        </div>
      </div>

      {isLoading ? (
        <div className="text-zinc-500">{t("library.loading")}</div>
      ) : (
        <div className="rounded-lg border border-zinc-800 overflow-hidden bg-zinc-900/30">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-zinc-900 text-zinc-400 font-medium">
                <tr>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3 w-24">Size</th>
                  <th className="px-4 py-3 w-32">Date</th>
                  <th className="px-4 py-3 w-24 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/50">
                {torrents?.map((torrent: Torrent) => (
                  <tr
                    key={torrent.id}
                    className="group hover:bg-zinc-900/50 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        {torrent.film?.poster ? (
                          <img
                            src={
                              torrent.film.poster.startsWith("http")
                                ? torrent.film.poster
                                : `https://image.tmdb.org/t/p/w92${torrent.film.poster}`
                            }
                            alt={torrent.film.name}
                            className="w-8 h-12 object-cover rounded bg-zinc-800"
                          />
                        ) : (
                          <div className="w-8 h-12 bg-zinc-800 rounded flex items-center justify-center text-xs text-zinc-600">
                            ?
                          </div>
                        )}
                        <div className="min-w-0">
                          <div
                            className="font-medium text-zinc-200 line-clamp-2"
                            title={torrent.name}
                          >
                            {torrent.name}
                          </div>
                          {torrent.film && (
                            <div className="text-xs text-violet-400 mt-0.5 truncate">
                              Linked: {torrent.film.name} ({torrent.film.year})
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-zinc-500 font-mono text-xs">
                      {(torrent.sz / 1024 / 1024 / 1024).toFixed(2)} GB
                    </td>
                    <td className="px-4 py-3 text-zinc-500 text-xs">
                      {new Date(torrent.created).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Button
                        size="sm"
                        variant="secondary"
                        className="h-8 text-xs bg-zinc-800 hover:bg-zinc-700"
                        onClick={() => {
                          void (async () => {
                            try {
                              await downloadTorrent(torrent.id);
                              toast.success(t("library.download_started"));
                            } catch (e) {
                              console.error(e);
                              toast.error(t("library.download_failed"));
                            }
                          })();
                        }}
                      >
                        <Download className="size-3 mr-1.5" />
                        {t("library.download")}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {torrents?.length === 0 && (
            <div className="py-12 text-center text-zinc-500 border-t border-zinc-800">
              {t("library.no_films")}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
export default LibraryPage;
