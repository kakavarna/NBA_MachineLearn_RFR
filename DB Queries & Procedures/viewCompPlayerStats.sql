WITH RecentStats AS (
    SELECT 
        player_id, 
        ps.game_id, 
        ps.season, 
        ps.firstName, 
        ps.lastName, 
        ps.teamName, 
        ps.teamCode, 
        ps.minutes, 
        ps.points, 
        ps.fgm, 
        ps.fga, 
        ps.fgp, 
        ps.ftm, 
        ps.fta, 
        ps.ftp, 
        ps.tpm, 
        ps.tpa, 
        ps.tpp, 
        ps.totReb, 
        ps.assists, 
        ps.steals, 
        ps.blocks,
        ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY ga.date DESC) AS game_rank
    FROM tbl_playerstats ps
    INNER JOIN view_train ga ON ga.GameID = ps.game_id
    WHERE ga.date > DATE_ADD(NOW(), INTERVAL -3 MONTH)
),
longGames AS (
    SELECT 
        player_id,
        ROUND(AVG(minutes),2) AS avg_minutes_long,
        ROUND(AVG(points),2) AS avg_pts_long,
        ROUND(AVG(tpm),2) AS avg_tpm_long,
        ROUND(AVG(totReb),2) AS avg_reb_long,
        ROUND(AVG(assists),2) AS avg_ast_long,
        ROUND(AVG(points + totReb + assists),2) AS avg_pra_long,
        ROUND(AVG(points + totReb),2) AS avg_pr_long,
        ROUND(AVG(points + assists),2) AS avg_pa_long,
        ROUND(AVG(totReb + assists),2) AS avg_ra_long
    FROM RecentStats
    WHERE game_rank <= 10
    GROUP BY player_id
),
shortGames AS (
    SELECT 
        player_id,
        ROUND(AVG(minutes),2) AS avg_minutes_short,
        ROUND(AVG(points),2) AS avg_pts_short,
        ROUND(AVG(tpm),2) AS avg_tpm_short,
        ROUND(AVG(totReb),2) AS avg_reb_short,
        ROUND(AVG(assists),2) AS avg_ast_short,
        ROUND(AVG(points + totReb + assists),2) AS avg_pra_short,
        ROUND(AVG(points + totReb),2) AS avg_pr_short,
        ROUND(AVG(points + assists),2) AS avg_pa_short,
        ROUND(AVG(totReb + assists),2) AS avg_ra_short
    FROM RecentStats
    WHERE game_rank <= 3
    GROUP BY player_id
),
RecentGame AS (
    SELECT 
        player_id, 
        teamName, 
        teamCode, 
        firstName, 
        lastName
    FROM RecentStats
    WHERE game_rank = 1 -- Ensures we get only the most recent game for player details
)
SELECT 
    rg.player_id, 
    rg.teamName, 
    rg.teamCode,
    rg.firstName, 
    rg.lastName,
    sg.avg_pts_short,
    lg.avg_pts_long,
    sg.avg_pts_short-lg.avg_pts_long AS PtsChange,
    sg.avg_tpm_short,
    lg.avg_tpm_long,
    sg.avg_tpm_short-lg.avg_tpm_long AS TpmChange,
    sg.avg_reb_short,
    lg.avg_reb_long,
    sg.avg_reb_short-lg.avg_reb_long AS RebChange,
    sg.avg_ast_short,
    lg.avg_ast_long,
    sg.avg_ast_short-lg.avg_ast_long AS AstChange,
    sg.avg_pra_short,
    lg.avg_pra_long,
    sg.avg_pr_short,
    lg.avg_pr_long,
    sg.avg_pa_short,
    lg.avg_pa_long,
    sg.avg_ra_short,
    lg.avg_ra_long,
    sg.avg_minutes_short,
    lg.avg_minutes_long
FROM longGames lg
JOIN shortGames sg ON lg.player_id = sg.player_id
JOIN RecentGame rg ON rg.player_id = lg.player_id
