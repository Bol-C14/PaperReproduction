; benchmark generated from python API
(set-info :status unknown)
(declare-fun a () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(declare-fun c () (_ BitVec 16))
(assert
 (and (distinct (bvadd ((_ extract 15 0) (bvmul ((_ extract 15 0) a) ((_ extract 15 0) b))) ((_ extract 15 0) c)) (bvadd ((_ extract 15 0) c) ((_ extract 15 0) (bvmul ((_ extract 15 0) b) ((_ extract 15 0) a))))) true))
(check-sat)
