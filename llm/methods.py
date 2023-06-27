METHODS=[
{"file":"org/apache/hadoop/hbase/regionserver/ServerNonceManager.java", "content":
"""
/**
 * Starts the operation if operation with such nonce has not already succeeded.
 * If the operation is in progress, waits for it to end and checks whether it
 * has succeeded.
 * @param group     Nonce group.
 * @param nonce     Nonce.
 * @param stoppable Stoppable that terminates waiting (if any) when the server
 *     is stopped.
 * @return true if the operation has not already succeeded and can proceed;
 *     false otherwise.
 */
public boolean startOperation(long group, long nonce, Stoppable stoppable)
    throws InterruptedException {
  if (nonce == HConstants.NO_NONCE)
    return true;
  NonceKey nk = new NonceKey(group, nonce);
  OperationContext ctx = new OperationContext();
  while (true) {
    OperationContext oldResult = nonces.putIfAbsent(nk, ctx);
    if (oldResult == null)
      return true;

    // Collision with some operation - should be extremely rare.
    synchronized (oldResult) {
      int oldState = oldResult.getState();
      LOG.debug(Conflict detected by nonce : +nk +, +oldResult);
      if (oldState != OperationContext.WAIT) {
        return oldState == OperationContext.PROCEED; // operation ended
      }
      oldResult.setHasWait();
      oldResult.wait(this.conflictWaitIterationMs); // operation is still
                                                    // active... wait and loop
      if (stoppable.isStopped()) {
        throw new InterruptedException(Server stopped);
      }
    }
  }
}
"""
}
,
{"file":"org/apache/hadoop/hbase/master/MasterWalManager.java", "content":
"""
/**
 * Inspect the log directory to find dead servers which need recovery work
 * @return A set of ServerNames which aren't running but still have WAL files
 *     left in file system
 * @deprecated With proc-v2, we can record the crash server with procedure
 *     store, so do not need
 *             to scan the wal directory to find out the splitting wal directory
 * any more. Leave it here only because {@code RecoverMetaProcedure}(which is
 * also deprecated) uses it.
 */
@Deprecated
public Set<ServerName> getFailedServersFromLogFolders() throws IOException {
  boolean retrySplitting = !conf.getBoolean(
      WALSplitter.SPLIT_SKIP_ERRORS_KEY, WALSplitter.SPLIT_SKIP_ERRORS_DEFAULT);

  Set<ServerName> serverNames = new HashSet<>();
  Path logsDirPath = new Path(CommonFSUtils.getWALRootDir(conf),
                              HConstants.HREGION_LOGDIR_NAME);

  do {
    if (services.isStopped()) {
      LOG.warn("Master stopped while trying to get failed servers.");
      break;
    }
    try {
      if (!this.fs.exists(logsDirPath))
        return serverNames;
      FileStatus[] logFolders =
          CommonFSUtils.listStatus(this.fs, logsDirPath, null);
      // Get online servers after getting log folders to avoid log folder
      // deletion of newly checked in region servers . see HBASE-5916
      Set<ServerName> onlineServers =
          services.getServerManager().getOnlineServers().keySet();

      if (logFolders == null || logFolders.length == 0) {
        LOG.debug("No log files to split, proceeding...");
        return serverNames;
      }
      for (FileStatus status : logFolders) {
        FileStatus[] curLogFiles =
            CommonFSUtils.listStatus(this.fs, status.getPath(), null);
        if (curLogFiles == null || curLogFiles.length == 0) {
          // Empty log folder. No recovery needed
          continue;
        }
        final ServerName serverName =
            AbstractFSWALProvider.getServerNameFromWALDirectoryName(
                status.getPath());
        if (null == serverName) {
          LOG.warn(
              "Log folder " + status.getPath() +
              " doesn't look like its name includes a "
              +
              "region server name; leaving in place. If you see later errors about missing "
              + "write ahead logs they may be saved in this location.");
        } else if (!onlineServers.contains(serverName)) {
          LOG.info("Log folder " + status.getPath() + " doesn't belong "
                   + "to a known region server, splitting");
          serverNames.add(serverName);
        } else {
          LOG.info("Log folder " + status.getPath() +
                   " belongs to an existing region server");
        }
      }
      retrySplitting = false;
    } catch (IOException ioe) {
      LOG.warn("Failed getting failed servers to be recovered.", ioe);
      if (!checkFileSystem()) {
        LOG.warn("Bad Filesystem, exiting");
        Runtime.getRuntime().halt(1);
      }
      try {
        if (retrySplitting) {
          Thread.sleep(conf.getInt("hbase.hlog.split.failure.retry.interval",
                                   30 * 1000));
        }
      } catch (InterruptedException e) {
        LOG.warn("Interrupted, aborting since cannot return w/o splitting");
        Thread.currentThread().interrupt();
        retrySplitting = false;
        Runtime.getRuntime().halt(1);
      }
    }
  } while (retrySplitting);

  return serverNames;
}
"""
}
,
{"file":"org/apache/hadoop/hbase/master/procedure/SplitWALProcedure.java", "content":
"""
protected Flow executeFromState(MasterProcedureEnv env,
                                MasterProcedureProtos.SplitWALState state)
    throws ProcedureSuspendedException, ProcedureYieldException,
           InterruptedException {
  SplitWALManager splitWALManager =
      env.getMasterServices().getSplitWALManager();
  switch (state) {
  case ACQUIRE_SPLIT_WAL_WORKER:
    worker = splitWALManager.acquireSplitWALWorker(this);
    setNextState(MasterProcedureProtos.SplitWALState.DISPATCH_WAL_TO_WORKER);
    return Flow.HAS_MORE_STATE;
  case DISPATCH_WAL_TO_WORKER:
    assert worker != null;
    addChildProcedure(
        new SplitWALRemoteProcedure(worker, crashedServer, walPath));
    setNextState(MasterProcedureProtos.SplitWALState.RELEASE_SPLIT_WORKER);
    return Flow.HAS_MORE_STATE;
  case RELEASE_SPLIT_WORKER:
    boolean finished;
    try {
      finished = splitWALManager.isSplitWALFinished(walPath);
    } catch (IOException ioe) {
      if (retryCounter == null) {
        retryCounter =
            ProcedureUtil.createRetryCounter(env.getMasterConfiguration());
      }
      long backoff = retryCounter.getBackoffTimeAndIncrementAttempts();
      LOG.warn(
          "Failed to check whether splitting wal {} success, wait {} seconds to retry",
          walPath, backoff / 1000, ioe);
      setTimeout(Math.toIntExact(backoff));
      setState(ProcedureProtos.ProcedureState.WAITING_TIMEOUT);
      skipPersistence();
      throw new ProcedureSuspendedException();
    }
    splitWALManager.releaseSplitWALWorker(worker, env.getProcedureScheduler());
    if (!finished) {
      LOG.warn("Failed to split wal {} by server {}, retry...", walPath,
               worker);
      setNextState(
          MasterProcedureProtos.SplitWALState.ACQUIRE_SPLIT_WAL_WORKER);
      return Flow.HAS_MORE_STATE;
    }
    ServerCrashProcedure.updateProgress(env, getParentProcId());
    return Flow.NO_MORE_STATE;
  default:
    throw new UnsupportedOperationException("unhandled state=" + state);
  }
}
"""
}
,
{"file":"org/apache/hadoop/hbase/master/procedure/InitMetaProcedure.java", "content":
"""
protected Flow executeFromState(MasterProcedureEnv env, InitMetaState state)
    throws ProcedureSuspendedException, ProcedureYieldException,
           InterruptedException {
  LOG.debug("Execute {}", this);
  try {
    switch (state) {
    case INIT_META_WRITE_FS_LAYOUT:
      Configuration conf = env.getMasterConfiguration();
      Path rootDir = CommonFSUtils.getRootDir(conf);
      TableDescriptor td = writeFsLayout(rootDir, conf);
      env.getMasterServices().getTableDescriptors().update(td, true);
      setNextState(InitMetaState.INIT_META_ASSIGN_META);
      return Flow.HAS_MORE_STATE;
    case INIT_META_ASSIGN_META:
      LOG.info("Going to assign meta");
      addChildProcedure(env.getAssignmentManager().createAssignProcedures(
          Arrays.asList(RegionInfoBuilder.FIRST_META_REGIONINFO)));
      setNextState(InitMetaState.INIT_META_CREATE_NAMESPACES);
      return Flow.HAS_MORE_STATE;
    case INIT_META_CREATE_NAMESPACES:
      LOG.info("Going to create {} and {} namespaces", DEFAULT_NAMESPACE,
               SYSTEM_NAMESPACE);
      createDirectory(env, DEFAULT_NAMESPACE);
      createDirectory(env, SYSTEM_NAMESPACE);
      // here the TableNamespaceManager has not been initialized yet, so we have
      // to insert the record directly into meta table, later the
      // TableNamespaceManager will load these two namespaces when starting.
      insertNamespaceToMeta(env.getMasterServices().getConnection(),
                            DEFAULT_NAMESPACE);
      insertNamespaceToMeta(env.getMasterServices().getConnection(),
                            SYSTEM_NAMESPACE);

      return Flow.NO_MORE_STATE;
    default:
      throw new UnsupportedOperationException("unhandled state=" + state);
    }
  } catch (IOException e) {
    if (retryCounter == null) {
      retryCounter =
          ProcedureUtil.createRetryCounter(env.getMasterConfiguration());
    }
    long backoff = retryCounter.getBackoffTimeAndIncrementAttempts();
    LOG.warn("Failed to init meta, suspend {}secs", backoff, e);
    setTimeout(Math.toIntExact(backoff));
    setState(ProcedureProtos.ProcedureState.WAITING_TIMEOUT);
    skipPersistence();
    throw new ProcedureSuspendedException();
  }
}
"""
}
,
{"file":"org/apache/hadoop/hbase/master/procedure/SwitchRpcThrottleProcedure.java", "content":
"""
protected Flow executeFromState(MasterProcedureEnv env,
                                SwitchRpcThrottleState state)
    throws ProcedureSuspendedException, ProcedureYieldException,
           InterruptedException {
  switch (state) {
  case UPDATE_SWITCH_RPC_THROTTLE_STORAGE:
    try {
      switchThrottleState(env, rpcThrottleEnabled);
    } catch (IOException e) {
      if (retryCounter == null) {
        retryCounter =
            ProcedureUtil.createRetryCounter(env.getMasterConfiguration());
      }
      long backoff = retryCounter.getBackoffTimeAndIncrementAttempts();
      LOG.warn("Failed to store rpc throttle value {}, sleep {} secs and retry",
               rpcThrottleEnabled, backoff / 1000, e);
      setTimeout(Math.toIntExact(backoff));
      setState(ProcedureProtos.ProcedureState.WAITING_TIMEOUT);
      skipPersistence();
      throw new ProcedureSuspendedException();
    }
    setNextState(SwitchRpcThrottleState.SWITCH_RPC_THROTTLE_ON_RS);
    return Flow.HAS_MORE_STATE;
  case SWITCH_RPC_THROTTLE_ON_RS:
    SwitchRpcThrottleRemoteProcedure[] subProcedures =
        env.getMasterServices()
            .getServerManager()
            .getOnlineServersList()
            .stream()
            .map(
                sn
                -> new SwitchRpcThrottleRemoteProcedure(sn, rpcThrottleEnabled))
            .toArray(SwitchRpcThrottleRemoteProcedure[] ::new);
    addChildProcedure(subProcedures);
    setNextState(SwitchRpcThrottleState.POST_SWITCH_RPC_THROTTLE);
    return Flow.HAS_MORE_STATE;
  case POST_SWITCH_RPC_THROTTLE:
    ProcedurePrepareLatch.releaseLatch(syncLatch, this);
    return Flow.NO_MORE_STATE;
  default:
    throw new UnsupportedOperationException("unhandled state=" + state);
  }
}
"""
}
,
{"file":"org/apache/hadoop/hbase/master/procedure/ReopenTableRegionsProcedure.java", "content":
"""
protected Flow executeFromState(MasterProcedureEnv env,
                                ReopenTableRegionsState state)
    throws ProcedureSuspendedException, ProcedureYieldException,
           InterruptedException {
  switch (state) {
  case REOPEN_TABLE_REGIONS_GET_REGIONS:
    if (!isTableEnabled(env)) {
      LOG.info("Table {} is disabled, give up reopening its regions",
               tableName);
      return Flow.NO_MORE_STATE;
    }
    List<HRegionLocation> tableRegions =
        env.getAssignmentManager().getRegionStates().getRegionsOfTableForReopen(
            tableName);
    regions = getRegionLocationsForReopen(tableRegions);
    setNextState(ReopenTableRegionsState.REOPEN_TABLE_REGIONS_REOPEN_REGIONS);
    return Flow.HAS_MORE_STATE;
  case REOPEN_TABLE_REGIONS_REOPEN_REGIONS:
    for (HRegionLocation loc : regions) {
      RegionStateNode regionNode =
          env.getAssignmentManager().getRegionStates().getRegionStateNode(
              loc.getRegion());
      // this possible, maybe the region has already been merged or split, see
      // HBASE-20921
      if (regionNode == null) {
        continue;
      }
      TransitRegionStateProcedure proc;
      regionNode.lock();
      try {
        if (regionNode.getProcedure() != null) {
          continue;
        }
        proc =
            TransitRegionStateProcedure.reopen(env, regionNode.getRegionInfo());
        regionNode.setProcedure(proc);
      } finally {
        regionNode.unlock();
      }
      addChildProcedure(proc);
    }
    setNextState(ReopenTableRegionsState.REOPEN_TABLE_REGIONS_CONFIRM_REOPENED);
    return Flow.HAS_MORE_STATE;
  case REOPEN_TABLE_REGIONS_CONFIRM_REOPENED:
    regions =
        regions.stream()
            .map(env.getAssignmentManager().getRegionStates()::checkReopened)
            .filter(l -> l != null)
            .collect(Collectors.toList());
    if (regions.isEmpty()) {
      return Flow.NO_MORE_STATE;
    }
    if (regions.stream().anyMatch(loc -> canSchedule(env, loc))) {
      retryCounter = null;
      setNextState(ReopenTableRegionsState.REOPEN_TABLE_REGIONS_REOPEN_REGIONS);
      return Flow.HAS_MORE_STATE;
    }
    // We can not schedule TRSP for all the regions need to reopen, wait for a
    // while and retry again.
    if (retryCounter == null) {
      retryCounter =
          ProcedureUtil.createRetryCounter(env.getMasterConfiguration());
    }
    long backoff = retryCounter.getBackoffTimeAndIncrementAttempts();
    LOG.info(
        "There are still {} region(s) which need to be reopened for table {} are in "
            + "OPENING state, suspend {}secs and try again later",
        regions.size(), tableName, backoff / 1000);
    setTimeout(Math.toIntExact(backoff));
    setState(ProcedureProtos.ProcedureState.WAITING_TIMEOUT);
    skipPersistence();
    throw new ProcedureSuspendedException();
  default:
    throw new UnsupportedOperationException("unhandled state=" + state);
  }
}
"""
}
,
{"file":"org/apache/hadoop/hbase/master/replication/ModifyPeerProcedure.java", "content":
"""
protected Flow executeFromState(MasterProcedureEnv env,
                                PeerModificationState state)
    throws ProcedureSuspendedException, InterruptedException {
  switch (state) {
  case PRE_PEER_MODIFICATION:
    try {
      prePeerModification(env);
    } catch (IOException e) {
      LOG.warn(
          "{} failed to call pre CP hook or the pre check is failed for peer {}, "
              + "mark the procedure as failure and give up",
          getClass().getName(), peerId, e);
      setFailure(
          "master-" + getPeerOperationType().name().toLowerCase() + "-peer", e);
      releaseLatch(env);
      return Flow.NO_MORE_STATE;
    } catch (ReplicationException e) {
      throw suspend(
          env.getMasterConfiguration(),
          backoff
          -> LOG.warn(
              "{} failed to call prePeerModification for peer {}, sleep {} secs",
              getClass().getName(), peerId, backoff / 1000, e));
    }
    resetRetry();
    setNextState(PeerModificationState.UPDATE_PEER_STORAGE);
    return Flow.HAS_MORE_STATE;
  case UPDATE_PEER_STORAGE:
    try {
      updatePeerStorage(env);
    } catch (ReplicationException e) {
      throw suspend(
          env.getMasterConfiguration(),
          backoff
          -> LOG.warn(
              "{} update peer storage for peer {} failed, sleep {} secs",
              getClass().getName(), peerId, backoff / 1000, e));
    }
    resetRetry();
    setNextState(PeerModificationState.REFRESH_PEER_ON_RS);
    return Flow.HAS_MORE_STATE;
  case REFRESH_PEER_ON_RS:
    refreshPeer(env, getPeerOperationType());
    setNextState(nextStateAfterRefresh());
    return Flow.HAS_MORE_STATE;
  case SERIAL_PEER_REOPEN_REGIONS:
    try {
      reopenRegions(env);
    } catch (Exception e) {
      throw suspend(
          env.getMasterConfiguration(),
          backoff
          -> LOG.warn("{} reopen regions for peer {} failed,  sleep {} secs",
                      getClass().getName(), peerId, backoff / 1000, e));
    }
    resetRetry();
    setNextState(PeerModificationState.SERIAL_PEER_UPDATE_LAST_PUSHED_SEQ_ID);
    return Flow.HAS_MORE_STATE;
  case SERIAL_PEER_UPDATE_LAST_PUSHED_SEQ_ID:
    try {
      updateLastPushedSequenceIdForSerialPeer(env);
    } catch (Exception e) {
      throw suspend(
          env.getMasterConfiguration(),
          backoff
          -> LOG.warn(
              "{} set last sequence id for peer {} failed,  sleep {} secs",
              getClass().getName(), peerId, backoff / 1000, e));
    }
    resetRetry();
    setNextState(enablePeerBeforeFinish()
                     ? PeerModificationState.SERIAL_PEER_SET_PEER_ENABLED
                     : PeerModificationState.POST_PEER_MODIFICATION);
    return Flow.HAS_MORE_STATE;
  case SERIAL_PEER_SET_PEER_ENABLED:
    try {
      enablePeer(env);
    } catch (ReplicationException e) {
      throw suspend(
          env.getMasterConfiguration(),
          backoff
          -> LOG.warn(
              "{} enable peer before finish for peer {} failed,  sleep {} secs",
              getClass().getName(), peerId, backoff / 1000, e));
    }
    resetRetry();
    setNextState(
        PeerModificationState.SERIAL_PEER_ENABLE_PEER_REFRESH_PEER_ON_RS);
    return Flow.HAS_MORE_STATE;
  case SERIAL_PEER_ENABLE_PEER_REFRESH_PEER_ON_RS:
    refreshPeer(env, PeerOperationType.ENABLE);
    setNextState(PeerModificationState.POST_PEER_MODIFICATION);
    return Flow.HAS_MORE_STATE;
  case POST_PEER_MODIFICATION:
    try {
      postPeerModification(env);
    } catch (ReplicationException e) {
      throw suspend(
          env.getMasterConfiguration(),
          backoff
          -> LOG.warn(
              "{} failed to call postPeerModification for peer {},  sleep {} secs",
              getClass().getName(), peerId, backoff / 1000, e));
    } catch (IOException e) {
      LOG.warn("{} failed to call post CP hook for peer {}, "
                   + "ignore since the procedure has already done",
               getClass().getName(), peerId, e);
    }
    releaseLatch(env);
    return Flow.NO_MORE_STATE;
  default:
    throw new UnsupportedOperationException("unhandled state=" + state);
  }
}
"""
}
,
{"file":"org/apache/hadoop/hbase/master/replication/SyncReplicationReplayWALRemoteProcedure.java", "content":
"""
/**
 * Only truncate wals one by one when task succeed. The parent procedure will
 * check the first wal length to know whether this task succeed.
 */
private void truncateWALs(MasterProcedureEnv env) {
  String firstWal = wals.get(0);
  try {
    env.getMasterServices()
        .getSyncReplicationReplayWALManager()
        .finishReplayWAL(firstWal);
  } catch (IOException e) {
    // As it is idempotent to rerun this task. Just ignore this exception and
    // return.
    LOG.warn("Failed to truncate wal {} for peer id={}", firstWal, peerId, e);
    return;
  }
  for (int i = 1; i < wals.size(); i++) {
    String wal = wals.get(i);
    try {
      env.getMasterServices()
          .getSyncReplicationReplayWALManager()
          .finishReplayWAL(wal);
    } catch (IOException e1) {
      try {
        // retry
        env.getMasterServices()
            .getSyncReplicationReplayWALManager()
            .finishReplayWAL(wal);
      } catch (IOException e2) {
        // As the parent procedure only check the first wal length. Just ignore
        // this exception.
        LOG.warn("Failed to truncate wal {} for peer id={}", wal, peerId, e2);
      }
    }
  }
}
"""
 }
]

